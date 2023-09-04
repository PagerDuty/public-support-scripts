require 'httparty'
require 'csv'
require 'dotenv'
require 'json'
require 'optparse'
require 'logger'

# Class responsible for parsing CSV files and returning an array of custom fields.
class CSVtoCustomFieldParser
  # Initializes a new instance of CSVtoCustomFieldParser.
  #
  # @param csv_file [String] The path to the CSV file.
  # @param logger [Logger] The logger instance for logging information and errors.
  def initialize(csv_file, logger)
    @csv_file = csv_file
    @logger = logger
  end

  # Parse the CSV file and return an array of custom fields.
  #
  # @return [Array<Hash>] An array of hashes, each hash representing a custom field.
  def parse
    fields = []
    CSV.foreach(@csv_file, headers: true) do |row|
      @logger.info "Parsing row: #{row}"
      field_options = if row['field_type'] == 'multi_value_fixed' || row['field_type'] == 'single_value_fixed'
                        generate_field_options(row['field_options'])
                      else
                        row['field_options']
                      end

      params = {
        'data_type': row['data_type'],
        'name': convert_to_snake_case(row['name']),
        'display_name': row['display_name'],
        'description': row['description'],
        'field_type': row['field_type'],
        'field_options': field_options
      }
      fields << params
    end
    fields
  end

  private

  # Generate field options for multi or single select fields.
  #
  # @param values [String] A string containing the options, separated by semicolons.
  # @return [Array<Hash>] An array of hashes, each hash representing an option.
  def generate_field_options(values)
    @logger.info 'Generating Field Options'
    values.split(';').map do |value|
      {
        'data' => {
          'data_type' => 'string',
          'value' => value.strip
        }
      }
    end
  end

  # Convert a string to snake_case.
  #
  # @example Convert a string to snake_case
  #   convert_to_snake_case("test custom field 1")
  #   # => "test_custom_field_1"
  #
  # @param input [String] The string to convert.
  # @return [String] The converted string.
  def convert_to_snake_case(input)
    result = input.gsub(' ', '_').downcase
    @logger.info "Converted #{input} to snake_case: #{result}"
    result
  end
end

########################################################################################
########################################################################################

# Class responsible for making API calls to create custom fields
class PagerDutyCustomFieldCreator
  include HTTParty
  base_uri 'https://api.pagerduty.com'
  headers 'Content-Type' => 'application/json'

  # Initializes a new instance of PagerDutyCustomFieldCreator.
  #
  # @param api_token [String] The PagerDuty API token.
  # @param logger [Logger] The logger instance for logging information and errors.
  def initialize(api_token, logger)
    @api_token = api_token
    @logger = logger
    @existing_fields = fetch_existing_custom_fields
  end

  # Sends an API request to PagerDuty to create a custom field.
  #
  # @param params [Hash] A hash containing the custom field parameters.
  # @return [Hash, nil] A hash containing the response from the API, or nil if the request was unsuccessful.
  # @see {PagerDuty API Documentation}[https://developer.pagerduty.com/api-reference/0f6094f852517-update-custom-field-values]
  def create_custom_field(params)
    endpoint = '/incidents/custom_fields'
    options = {
      body: { 'field': params }.to_json,
      headers: { 'Authorization' => "Token token=#{@api_token}" }
    }

    @logger.debug 'Calling private function to determine if custom field exists'
    if check_existing_custom_field(params[:name])
      @logger.info "Skipping attempt to create #{params[:name]}: already exists."
      puts "Skipping creation of #{params[:name]}"
      puts "     a custom field by that name alread exists on this api-key's account."
      return { 'status' => 'skipped' }
    end

    @logger.info "Sending POST request to #{endpoint} with body: #{options[:body]}"
    response = self.class.post(endpoint, options)
    parsed_response = JSON.parse(response.body)

    if response.success?
      @logger.info "Successfully created custom field. Response: #{parsed_response}"
      parsed_response
    else
      handle_api_error(parsed_response)
    end
  rescue HTTParty::Error => e
    handle_connection_error(e)
  end

  private

  # Fetches existing custom fields from PagerDuty.
  #
  # @return [Array, false] List of existing fields or false if request failed.
  def fetch_existing_custom_fields
    endpoint = '/incidents/custom_fields'
    options = {
      headers: {
        'Authorization' => "Token token=#{@api_token}",
        'Content-Type' => 'application/json'
      }
    }
    @logger.info "Making call to get existing field names from #{endpoint}"
    response = self.class.get(endpoint, options)
    @logger.info "The following response was received: #{response}"
    if response.success?
      json = JSON.parse(response.body)
      @logger.info "The following parsing is being stored: #{json}"
      json
    else
      handle_api_error(JSON.parse(response.body))
    end
  rescue HTTParty::Error => e
    handle_connection_error(e)
  end

  # Checks if a custom field with the provided name already exists.
  #
  # @param field_name [String] The name of the custom field to check for.
  # @return [Boolean] Returns true if the custom field with the given name exists,
  # otherwise returns false (including if it is unabel to determine the result).
  def check_existing_custom_field(field_name)
    return false unless @existing_fields

    existing_field = @existing_fields['fields'].find { |field| field['name'] == field_name }

    # Log and bool-report whether field was found
    if existing_field
      @logger.warn "Found existing custom field with name '#{field_name}'."
      true
    else
      @logger.info "No existing custom field found with name '#{field_name}'."
      false
    end
  end

  # Handles API errors by logging and displaying them.
  #
  # @param response [Hash] The parsed API response.
  def handle_api_error(response)
    error_message = if response['error']
                      "#{response['error']['code']}: #{response['error']['errors'].join(', ')}"
                    else
                      "Unexpected error: #{response}"
                    end
    @logger.error error_message
    puts error_message
    false
  end

  # Handles HTTParty connection errors by logging and displaying them.
  #
  # @param error [HTTParty::Error] The raised error.
  def handle_connection_error(error)
    error_message = "Connection error: #{error.message}"
    @logger.error error_message
    puts error_message
    false
  end
end

########################################################################################
########################################################################################

# Validates the existence of the API key.
#
# @param api_key [String] The API key.
def check_api_key(api_key)
  return unless api_key.nil? || api_key.empty?

  logger.info 'ERROR: `PAGERDUTY_API_KEY` not found.'
  puts "PAGERDUTY_API_KEY not found. Please ensure it's set in your .env file or environment variables."
  puts "If you'd like to add it in a local file and you are in this script's root directory just run:"
  puts '        cp fake.env .env; nano .env'
  puts "Alternately: you can pass the key directly by prepending `PAGERDUTY_API_KEY='#####' to this script's call."
  puts "e.g.:   PAGERDUTY_API_KEY='#####' bundle exec ruby import_custom_fields.rb --file my_custom_fields.csv"
  exit(1) # Exit the script with an error code.
end

# #################################################################################### #
# Usage:
# #################################################################################### #

# Run the following only if this file is run directly (vs, for example, from a tester)
if __FILE__ == $0

  # Create logger object
  logger = Logger.new('application.log')
  logger.info 'Starting application'

  # load env (including `.env` file values)
  Dotenv.load

  # Ensure presence of API key
  env_api_key = ENV['PAGERDUTY_API_KEY']
  check_api_key(env_api_key)

  # CLI Argument/Option handling
  options = {}
  OptionParser.new do |opts|
    opts.banner = 'Usage: ruby PD_custom_field_CSV_import.rb [options]'
    opts.on('-f', '--file FILE', 'CSV file path') do |file|
      options[:file] = file
    end
  end.parse!

  unless options[:file]
    logger.info 'ERROR: csv file path argument not received'
    puts 'A CSV file path is required.'
    puts 'example: `... --file my_custom_fields.csv`'
    puts 'That would tell the script to use the "my_custom_fields" csv file in the current directory'
    exit(1)
  end

  # Generate parser and extract usable custom_fields
  logger.info 'Parsing CSV file'
  parser = CSVtoCustomFieldParser.new(options[:file], logger)
  fields = parser.parse
  logger.info "Finished parsing CSV file. Fields: #{fields}"

  # Generate field-creator and make consecutive api calls
  logger.info 'Creating custom fields'
  creator = PagerDutyCustomFieldCreator.new(env_api_key, logger)
  fields.each do |field|
    result = creator.create_custom_field(field)
    if result
      if result['status'] == 'skipped'
        # skip
      else
        message = "Custom field created: #{field[:name]} with ID: #{result['field']['id']}"
        logger.info message
        puts message
      end
    else
      message = "Failed to create custom field with name: #{field[:name]}"
      logger.error message
      puts message
    end
  end
  puts 'You can inspect custom fields present on your acount at:'
  puts 'https://<your_domain>.pagerduty.com/customfields/'
  logger.info 'Finished creating custom fields'
end
