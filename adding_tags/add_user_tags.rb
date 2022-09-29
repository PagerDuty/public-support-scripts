#!/usr/bin/env ruby

require 'rubygems'
require 'faraday'
require 'json'
require 'csv'
require 'optparse'
require 'logger'

class PagerDutyAgent
  attr_reader :token
  attr_reader :connection

  def initialize(token)
    @token = token
    @connection = Faraday.new(:url => "https://api.pagerduty.com",
                              :ssl => {:verify => true}) do |c|
      c.request  :url_encoded
      c.adapter  :net_http
    end
    #making an initial call to /users to extract subdomain corresponding to the API key
    initial = connection.get("/users", query = {}, { 'Authorization' => "Token token=#{token}",
          'Accept' => 'application/vnd.pagerduty+json;version=2'})
    users = JSON.parse(initial.body)['users']
    subdomain = users[0]['html_url'][/https:\/\/(.*)\.pagerduty\.com.*/, 1]
    puts("Adding user tags for #{subdomain}, proceed? (y/n)")
    #evaluating agent input
    decision = ""
    while decision.chomp != "y"
      decision = gets
      if decision.chomp == "n"
        abort "Discontinuing user import"
      end
    end
      #logger defined as a global variable accessible to all classes in the script
      $log = Logger.new("import_errors_for_#{Date.today}.log")
  end

  def get(path, query = {})
    response = connection.get(path, query,
        { 'Authorization' => "Token token=#{token}",
          'Accept' => 'application/vnd.pagerduty+json;version=2'})
    if !response.success?
      $log.error("Status: #{response.status}
        Response: #{response.body}---Query: #{query}")
      raise "Error: #{response.body}"
    end
    JSON.parse(response.body)
  end

  def post(path, body = {}, extra_headers = nil)
    body_json = JSON.generate(body)
    if @extra_headers
      headers = { 'Authorization' => "Token token=#{token}",
        'Content-Type' => 'application/json',
        'Accept' => 'application/vnd.pagerduty+json;version=2'}
    else
      headers = { 'Authorization' => "Token token=#{token}",
        'Content-Type' => 'application/json',
        'Accept' => 'application/vnd.pagerduty+json;version=2'}
    end
    response = connection.post(path, body_json, headers)

    if !response.success?
      $log.error("Status: #{response.status}--Response: #{response.body}---Payload: #{body}")
      raise "Error: #{response.body}"
    end

    return JSON.parse(response.body)
  end

  def find_user_by_email(email)
    get("/users", :query => email)
  end

  def add_tags(user_id, tag)
      tags = tag.map do |t|
        {
          :type => "tag",
          :label => t
        }
      end

    request_body = {
      :add => tags,
      :remove => [
        {
          :type => nil,
          :id => nil
        }
      ]
    }
    post("/users/#{user_id}/change_tags", request_body)
  end

end

class CSVImporter

  Record = Struct.new(:email, :tags)

  attr_reader :agent
  attr_reader :csv_file

  def initialize(agent, csv_file)
    @agent = agent
    @csv_file = csv_file
  end

  def import_user(record)
    $log.info("Attempting to find existing user by email #{record.email}.")
    # Try to find an existing user
    users = agent.find_user_by_email(record.email)
    user = nil; user_id = nil

    if users["users"].size > 0
      # FIXME: Make sure this is actually the user and not just the first user
      user = users["users"][0]
      user_id = user["id"]

    puts "Found user: #{record.email}."
    $log.info("Found existing user #{record.email}.")

    tags = record.tags.split(",")
    puts "adding tags to user #{record.email}"
    $log.info("Adding tags to user: #{record.email}")
    agent.add_tags(user_id, tags)
    puts "#{tags} added"
    $log.info("#{tags} added")
    else
      puts "No user found with email #{record.email}!"
      $log.error("No user found with email #{record.email}!")
    end

  rescue Exception => e
    puts "Error adding or updating user: #{record}, #{e}."
  end

  def import
    CSV.foreach(csv_file).with_index(1) do |row, index|
      next if index == 1
      import_user(row_to_record(row))
    end
  end

  def row_to_record(row)
    # NOTE: You may need to adjust this if the format of your row is different.
    Record.new(row[0], row[1])
  end
end

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: import_users.rb [options]"
  opts.on('-a', '--access-token [String]', 'Access Token') do |a|
    options[:access_token] = a
  end
  opts.on('-f', '--csv-path [String]', 'Path to CSV file') do |f|
    options[:csv_path] = f
  end
end.parse!

agent = PagerDutyAgent.new(options[:access_token])

CSVImporter.new(agent, options[:csv_path]).import
