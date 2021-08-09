#!/usr/bin/env ruby

require 'rubygems'
require 'faraday'
require 'json'
require 'csv'
require 'optparse'
require 'logger'

class PagerDutyAgent
  attr_reader :token
  attr_reader :requester_email
  attr_reader :no_new_teams
  attr_reader :connection

  def initialize(token, requester_email, no_new_teams)
    @requester_email = requester_email
    @token = token
    @no_new_teams = no_new_teams
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
    puts("About to perform user import for #{subdomain}, proceed? (y/n)")
    #evaluating agent input
    decision = ""
    while decision.chomp != "y"
      decision = gets
      if decision.chomp == "n"
      abort "Discontinuing user import"
    end
    end
    #logger defined as a global variable accessible to all classes in the script
    $log = Logger.new("import_errors_for_#{requester_email}.log")
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
        'From' => "#{$requester_email}",
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

  def put(path, body = {})
    response = connection.put(path, body,
      { 'Authorization' => "Token token=#{token}",
        'Accept' => 'application/vnd.pagerduty+json;version=2'})

    if !response.success?
      $log.error("Status: #{response.status}--Response: #{response.body}---Payload: #{body}")
      raise "Error: #{response.body}"
    end

    puts response.status
  end

  def add_user(name, email, role, title)
    request_body = {
      :user => {
        :name => name,
        :email => email,
        :role => role.downcase.strip,
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

  def add_user_to_team(team_id, user_id, team_role)
    request_body = {'role' => team_role}
    put("/teams/#{team_id}/users/#{user_id}", request_body)
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

  Record = Struct.new(:name, :email, :role, :title, :country_code, :phone_number, :teams, :team_roles)

  DEFAULT_TEAM_ROLES = {'owner': 'manager','admin': 'manager','user': 'manager','limited_user': 'responder','ready_only_user': 'observer',
                         'ready_only_limited_user': 'observer', 'observer': 'observer'}.freeze

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
      puts "Found contact methods: #{agent.contact_methods(user_id)}."
      $log.info("Found existing contact methods #{record.email}.")
      puts ""
    else
      # Default role to user
      record.role = "user" if !record.role
      # Default title to " "
      record.title = " " if !record.title
      puts "Adding user: #{record.name}."
      $log.info("Attempting to add user #{record.name}.")
      $log.info("User's record details: #{record}.")
      # verifying if country code value is either null or numeric string
      # the contrary may suggest commas in user's title
      unless (record.to_a[4].nil? || record.to_a[4].to_i != 0 || record.to_a[4] == " ")
        puts("Title property for #{record.email} may include commas, proceed? y/n")
        #evaluating agent input
        decision = ""
        while decision.chomp != "y"
        decision = gets
        if decision.chomp == "n"
        $log.error("User#{record.email} was not imported due to title property misconfiguration")
        abort "Discontinuing user import for #{record.email}"
        end
        end
      end
      user = agent.add_user(record.name, record.email, record.role.downcase, record.title)
      user_id = user["user"]["id"]
      puts "Added user with ID #{user_id}."
      $log.info("Created a new user with ID #{user_id} and login email #{record.email}.")
    end

    # Add user to teams
    puts "Adding user to teams."
    $log.info("Adding user #{record.name} to teams.")
    teams = record.teams ? record.teams.split(";") : []

    teams.each_with_index do |team,team_index|
      team_role = team_roles(record,team_index)
      team_id = agent.get_team_id(agent.find_teams_by_name(team.strip)["teams"], team.strip)

      if team_id
        agent.add_user_to_team(team_id, user_id, team_role)
        puts "Added #{record.name} to team #{team}"
        $log.info("Added #{record.name} to team #{team}")
        puts "Role #{team_role} applied to #{team} team for #{record.name}"
        $log.info("Role #{team_role} applied to #{team} team for #{record.name}")
      elsif agent.no_new_teams
        puts "Could not find team #{team}, skipping."
        $log.info("Could not find team #{team}, skipping.")
      else
        puts "Could not find team #{team}, creating a new team."
        $log.info("Could not find existing team #{team}, creating a new team.")
        r = agent.add_team(team.strip)
        team_id = r['team']['id']
        puts "Created team #{team} with ID #{team_id}, adding user to team."
        agent.add_user_to_team(team_id, user_id, team_role)
        puts "Added #{record.name} to #{team}, with role #{team_role}."
        $log.info("Added #{record.name} to team #{team}, with role #{team_role}.")
      end
    end

    # Add user and email notification rule
    ["SMS", "phone"].each do |type|
      if (!record.phone_number || !record.country_code)
        puts "Phone number and/or country code blank; skipping creation of #{type} contact method and notification rules."
        $log.info("Phone number and/or country code blank; skipping creation of #{type} contact method and notification rules.")
      else
        add_contact_method(type, user_id, record)
      end
    end

  rescue Exception => e
    puts "Error adding or updating user: #{record}, #{e}."
  end

  # type: phone, SMS, email
  def add_contact_method(type, user_id, record)
    puts "Adding #{type} notification."
    $log.info("Attempting to add #{type} notification for user #{record.name}.")
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
      $log.info(row)
      import_user(row_to_record(row))
    end
  end

  def row_to_record(row)
    # NOTE: You may need to adjust this if the format of your row is different.
    Record.new(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
  end

  private

  def team_roles(record,team_index)
    #role must be one of the following manager,observer,responder in the csv file as per our API
    user_role = record.role

    #return observer as fixed role if base role is one of the ready_only
    return 'observer' if user_role.include?('read_only')

    default_role = DEFAULT_TEAM_ROLES["#{user_role}".to_sym]

    #return manager as fixed role if base role is either admin or owner
    return 'manager' if user_role == 'owner' || user_role == 'admin'

    team_roles = record.team_roles ? record.team_roles.split(";") : []

    # return first role if there is only one
    return team_roles[0] if team_roles.length == 1

    #replace all the blank array elements with the default
    team_roles.map! { |r| r&.empty? ? default_role : r }

    #return team role associated with the team OR return default team role
    team_roles[team_index] || default_role
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
  opts.on('-n', '--[no-]no-new-teams', 'If a non-existing team is named in the file, skip') do |n|
    options[:no_new_teams] = n
  end
end.parse!

agent = PagerDutyAgent.new(options[:access_token], options[:requester_email], options[:no_new_teams])

CSVImporter.new(agent, options[:csv_path]).import
