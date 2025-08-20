require 'faraday'
require 'json'
require 'csv'
require 'optparse'
require 'logger'

class PagerDutyAPI
  def initialize(api_token, logger)
    @connection = Faraday.new(url: 'https://api.pagerduty.com') do |faraday|
      faraday.request :url_encoded
      faraday.adapter Faraday.default_adapter
    end

    @headers = {
      'Authorization' => "Token token=#{api_token}",
      'Content-Type' => 'application/json',
      'Accept' => 'application/vnd.pagerduty+json;version=2'
    }

    @logger = logger
  end

  def fetch_webhook_subscriptions
    response = @connection.get('/webhook_subscriptions', nil, @headers)
    if response.success?
      JSON.parse(response.body)['webhook_subscriptions']
    else
      @logger.error("Failed to fetch subscriptions. Status: #{response.status}, Response: #{response.body}")
      abort("Failed to fetch subscriptions. Status: #{response.status}, Response: #{response.body}")  
    end
  end

  def activate_subscription(subscription_id)
    body = {
      webhook_subscription: {
        active: true
      }
    }.to_json

    response = @connection.put("/webhook_subscriptions/#{subscription_id}", body, @headers)

    if response.success?
      @logger.info("Webhook subscription #{subscription_id} activated successfully.")
      puts "Webhook subscription #{subscription_id} activated successfully"
    else
      @logger.error("Failed to activate webhook subscription #{subscription_id}. Status: #{response.status}, Response: #{response.body}")
       abort("Failed to activate webhook subscription #{subscription_id}. Status: #{response.status}, Response: #{response.body}")
    end
  end
end

class PagerDutyWebhookSubscription
  def initialize(api)
    @api = api
  end

  def process_inactive_subscriptions
    subscriptions = @api.fetch_webhook_subscriptions
    inactive_subscriptions = subscriptions.select { |sub| !sub['active'] }
    count = inactive_subscriptions.length

    if inactive_subscriptions.empty?
      puts "There are no inactive webhook subscriptions."
      exit
    else
      puts "There are #{count} Inactive Webhook Subscriptions:"
      inactive_subscriptions.each do |sub|
        puts "ID: #{sub['id']}, Name: #{sub['description']}"
      end

      save_inactive_subscriptions_to_csv(inactive_subscriptions)

      puts ""
      puts "********************************************************************"
      puts "Do you want to enable the inactive webhook subscriptions? (yes/no)"
      puts "********************************************************************"

      user_input = gets.chomp.downcase

      if user_input == 'yes'
        inactive_subscriptions.each do |sub|
          @api.activate_subscription(sub['id'])
        end
      else
        puts "No subscriptions were activated."
      end
    end
  end

  def activate_subscriptions_from_csv(file_path)
    CSV.foreach(file_path, headers: true) do |row|
      subscription_id = row['subscription_id']
      @api.activate_subscription(subscription_id)
    end
  end

  private

  def save_inactive_subscriptions_to_csv(subscriptions)
    CSV.open('inactive_subscriptions.csv', 'w') do |csv|
      csv << ['subscription_id', 'description']
      subscriptions.each do |sub|
        csv << [sub['id'], sub['description']]
      end
    end
    puts "Inactive subscriptions have been downloaded to inactive_subscriptions.csv file."
  end
end

class CommandLineParser
  attr_reader :options

  def initialize(args = ARGV)
    @options = {}
    parse_options(args)
    validate_options
  end

  private

  def parse_options(args)
    OptionParser.new do |opts|
      opts.banner = "Usage: webhook_subscription.rb [options]"

      opts.on("-a", "--api-token API_TOKEN", "PagerDuty API token") do |v|
        @options[:api_token] = v
      end

      opts.on("-f", "--file PATH", "Path to the CSV file (required with -e)") do |v|
        @options[:file_path] = v
      end

      opts.on("-e", "--execute ACTION", "Action to perform (activate_wsub)") do |v|
        @options[:action] = v
      end
    end.parse!(args)
  end

  def validate_options
    if @options[:api_token].nil?
      puts "API token is required."
      exit
    end

    if @options[:action] == 'activate_wsub' && @options[:file_path].nil?
      puts "CSV file path is required for activation."
      exit
    elsif @options[:file_path] && @options[:action] != 'activate_wsub'
      puts "The -f option requires the -e option with 'activate_wsub'."
      exit
    end
  end
end

# Main script execution
def main
  options = CommandLineParser.new.options
  logger = Logger.new('pagerduty_webhook.log')
  logger.level = Logger::DEBUG
  #logger = Logger.new(STDOUT)

  api = PagerDutyAPI.new(options[:api_token], logger)
  manager = PagerDutyWebhookSubscription.new(api)

  if options[:action] == 'activate_wsub'
    manager.activate_subscriptions_from_csv(options[:file_path])
  else
    manager.process_inactive_subscriptions
  end
end

main if __FILE__ == $PROGRAM_NAME
