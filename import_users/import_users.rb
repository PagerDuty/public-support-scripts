#!/usr/bin/env ruby

require 'rubygems'
require 'faraday'
require 'json'
require 'csv'
require 'optparse'

class PagerDutyAgent
  attr_reader :token
  attr_reader :requester_email
  attr_reader :create_teams
  attr_reader :connection

  def initialize(token, requester_email, create_teams)
    @token = token
    @requester_email = requester_email
    @create_teams = create_teams
    @connection = Faraday.new(:url => "https://api.pagerduty.com",
                              :ssl => {:verify => true}) do |c|
      c.request  :url_encoded
      c.adapter  :net_http
    end
  end

  def get(path, query = {})
    response = connection.get(path, query,
        { 'Authorization' => "Token token=#{token}",
          'Accept' => 'application/vnd.pagerduty+json;version=2'})
    raise "Error: #{response.body}" unless response.success?
    JSON.parse(response.body)
  end

  def post(path, body = {}, extra_headers = nil)
    body_json = JSON.generate(body)
    if @extra_headers
      headers = { 'Authorization' => "Token token=#{token}",
        'Content-Type' => 'application/json',
        'From' => "#{requester_email}",
        'Accept' => 'application/vnd.pagerduty+json;version=2'}
    else
      headers = { 'Authorization' => "Token token=#{token}",
        'Content-Type' => 'application/json',
        'Accept' => 'application/vnd.pagerduty+json;version=2'}
    end
    response = connection.post(path, body_json, headers)
    raise "Error: #{response.body}" unless response.success?
    return JSON.parse(response.body)
  end

  def put(path, body = {})
    response = connection.put(path, body,
      { 'Authorization' => "Token token=#{token}",
        'Accept' => 'application/vnd.pagerduty+json;version=2'})
    raise "Error: #{response.body}" unless response.success?
    puts response.status
  end

  def add_user(name, email, role, title)
    request_body = {
      :user => {
        :name => name,
        :email => email,
        :role => role,
        :job_title => title
      }
    }
    post("/users", request_body, true)
  end

  def add_contact(user_id, type, address, country_code, label)
    if type == 'email'
      type = 'email_contact_method'
    elsif type == 'SMS'
      type = 'sms_contact_method'
    elsif type == 'phone'
      type = 'phone_contact_method'
    end
    request_body = {
      :contact_method => {
        :type => type,
        :address => address,
        :label => label
      }
    }
    request_body[:contact_method][:country_code] = country_code if ["sms_contact_method", "phone_contact_method"].include?(type)
    post("/users/#{user_id}/contact_methods", request_body)
  end

  def add_notification_rule(user_id, contact_method_id, contact_method_type, delay_in_minutes)
    request_body = {
      :notification_rule => {
        :start_delay_in_minutes => delay_in_minutes,
        :contact_method => {
            :id => contact_method_id,
            :type => contact_method_type
        }
      }
    }
    post("/users/#{user_id}/notification_rules", request_body)
  end

  def add_user_to_team(team_id, user_id)
    put("/teams/#{team_id}/users/#{user_id}")
  end

  def add_team(team_name)
    request_body = {'type' => 'team', 'name' => team_name}
    post("/teams", request_body)
  end

  def find_teams_by_name(name)
    get("/teams", :query => name)
  end

  def get_team_id(teams, name)
    teams.each do |team|
      return team["id"] if team["name"].downcase == name.downcase
    end
    return nil
  end

  def find_user_by_email(email)
    get("/users", :query => email)
  end

  def contact_methods(user_id)
    get("/users/#{user_id}/contact_methods")
  end

end

class CSVImporter

  Record = Struct.new(:name, :email, :role, :title, :country_code, :phone_number, :teams)

  attr_reader :agent
  attr_reader :csv_file

  def initialize(agent, csv_file)
    @agent = agent
    @csv_file = csv_file
  end

  def import_user(record)

    # Try to find an existing user
    users = agent.find_user_by_email(record.email)
    user = nil; user_id = nil

    if users["users"].size > 0
      # FIXME: Make sure this is actually the user and not just the first user
      user = users["users"][0]
      user_id = user["id"]
      puts "Found user: #{record.email}"
      puts "Found contact methods: #{agent.contact_methods(user_id)}"
      puts ""
    else
      # Default role to user
      record.role = "user" if !record.role
      # Default title to " "
      record.title = " " if !record.title
      puts "Adding user: #{record}"
      user = agent.add_user(record.name, record.email, record.role.downcase, record.title)
      user_id = user["user"]["id"]
      puts "Added user with id: #{user_id}"
    end

    # Add user and email notification rule
    ["SMS", "phone"].each do |type|
      add_contact_method(type, user_id, record)
    end

    # Add user to teams
    puts "Adding user to teams"
    teams = record.teams ? record.teams.split(";") : []
    teams.each do |team|
      team_id = agent.get_team_id(agent.find_teams_by_name(team.strip)["teams"], team.strip)
      if team_id
        agent.add_user_to_team(team_id, user_id)
      else
        if agent.create_teams
          puts "Could not find team #{team}, creating a new team..."
          r = agent.add_team(team)
          team_id = r['team']['id']
          puts "Created team #{team} with ID #{team_id}, adding user to team..."
          agent.add_user_to_team(team_id, user_id)
        else
          puts "Could not find team #{team}, skipping..."
        end
      end
    end

  rescue Exception => e
    puts "Error adding user: #{record}, #{e}"
  end

  # type: phone, SMS, email
  def add_contact_method(type, user_id, record)
    puts "Adding #{type} notification"
    contact_method = agent.add_contact(user_id, type,
      record.phone_number, record.country_code, "Mobile")
    contact_method_id = contact_method["contact_method"]["id"]
    contact_method_type = contact_method["contact_method"]["type"]
    agent.add_notification_rule(user_id, contact_method_id, contact_method_type, 0)
    # Add retries for phone notification
    if ["phone"].include?(type)
      agent.add_notification_rule(user_id, contact_method_id, contact_method_type, 3)
    end
  end

  def import
    CSV.foreach(csv_file) do |row|
      import_user(row_to_record(row))
    end
  end

  def row_to_record(row)
    # NOTE: You may need to adjust this if the format of your row is different.
    Record.new(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
  end

end

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: import_users.rb [options]"

  opts.on('-a', '--access-token [String]', 'Access Token') do |a|
    options[:access_token] = a
  end
  opts.on('-e', '--requester-email [String]', 'Requester Email') do |e|
    options[:requester_email] = e
  end
  opts.on('-f', '--csv-path [String]', 'Path to CSV file') do |f|
    options[:csv_path] = f
  end
  opts.on('-t', '--[no-]create-teams', 'Auto-provision teams that do not already exist') do |t|
    options[:create_teams] = t
  end
end.parse!

agent = PagerDutyAgent.new(options[:access_token], options[:requester_email], options[:create_teams])

CSVImporter.new(agent, options[:csv_path]).import
