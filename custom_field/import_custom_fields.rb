require 'httparty'
require 'csv'
require 'json'
require 'optparse'
require 'logger'

# Create logger object
logger = Logger.new('application.log')
logger.info 'Starting application'

# Class responsible for parsing CSV files and returning an array of custom fields.
class CSVtoCustomFieldParser
  # @param file [String] The path to the CSV file.
  # @param logger [Logger] The logger object
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

# Class responsible for making API calls to create custom fields
class PagerDutyCustomFieldCreator
  include HTTParty
  base_uri 'https://api.pagerduty.com'
  headers 'Content-Type' => 'application/json'

  attr_reader :api_token

  # @param api_token [String] The PagerDuty API token.
  # @param logger [Logger] The logger object
  def initialize(api_token, logger)
    @api_token = api_token
    @logger = logger
  end

  # Create a custom field in PagerDuty.
  #
  # @param params [Hash] A hash containing the custom field parameters.
  # @return [Hash, nil] A hash containing the response from the API, or nil if the request was unsuccessful.
  # @see {PagerDuty API Documentation}[https://developer.pagerduty.com/api-reference/0f6094f852517-update-custom-field-values]
  def create_custom_field(params)
    endpoint = '/incidents/custom_fields'

    options = {
      body: { 'field': params }.to_json,
      headers: { 'Authorization' => "Token token=#{api_token}" }
    }

    @logger.info "Sending POST request to #{endpoint} with body: #{options[:body]}"

    response = self.class.post(endpoint, options)
    parsed_response = JSON.parse(response.body)

    if response.success?
      @logger.info "Successfully created custom field. Response: #{parsed_response}"
      parsed_response
    else
      error_message = "#{parsed_response['error']['code']}: Error message  #{parsed_response['error']['errors']}"
      @logger.error error_message
      puts error_message
      nil
    end
  rescue HTTParty::Error => e
    error_message = "Error creating custom field: #{e}"
    @logger.error error_message
    puts error_message
    nil
  end
end

# #################################################################################### #
# Usage:
# #################################################################################### #

# Run the following only if this file is run directly (vs, for example, from a tester)
if __FILE__ == $0

  # CLI Argument/Option handling
  options = {}
  OptionParser.new do |opts|
    opts.banner = 'Usage: ruby PD_custom_field_CSV_import.rb [options]'

    opts.on('-k', '--api-key API_KEY', 'PagerDuty API key') do |api_key|
      options[:api_key] = api_key
    end

    opts.on('-f', '--file FILE', 'CSV file path') do |file|
      options[:file] = file
    end
  end.parse!

  unless options[:api_key] && options[:file]
    puts 'Both API key and CSV file path are required.'
    exit
  end

  # Generate parser and extract usable custom_fields
  logger.info 'Parsing CSV file'
  parser = CSVtoCustomFieldParser.new(options[:file], logger)
  fields = parser.parse
  logger.info "Finished parsing CSV file. Fields: #{fields}"

  # Generate field-creator and make consecutive api calls
  logger.info 'Creating custom fields'
  creator = PagerDutyCustomFieldCreator.new(options[:api_key], logger)
  fields.each do |field|
    result = creator.create_custom_field(field)
    if result
      message = "Custom field created: #{field[:name]} with ID: #{result['field']['id']}"
      logger.info message
      puts message
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
