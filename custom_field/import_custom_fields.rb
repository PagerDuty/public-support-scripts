require 'httparty'
require 'csv'
require 'json'
require 'optparse'


# Class responsible for parsing CSV files and returning an array of custom fields.
class CSVtoCustomFieldParser
  # @param file [String] The path to the CSV file.
  def initialize(csv_file)
    @csv_file = csv_file
  end

  # Parse the CSV file and return an array of custom fields.
  #
  # @return [Array<Hash>] An array of hashes, each hash representing a custom field.
  def parse
    fields = []
    CSV.foreach(@csv_file, headers: true) do |row|
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
    input.gsub(' ', '_').downcase
  end
end


# Class responsible for making API calls to create custom fields
class PagerDutyCustomFieldCreator
  include HTTParty
  base_uri 'https://api.pagerduty.com'
  headers 'Content-Type' => 'application/json'

  attr_reader :api_token

  # @param api_token [String] The PagerDuty API token.
  def initialize(api_token)
    @api_token = api_token
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

    response = self.class.post(endpoint, options)
    parsed_response = JSON.parse(response.body)

    if response.success?
      parsed_response
    else
      puts "#{parsed_response['error']['code']}: Error message  #{parsed_response['error']['errors']}"
      nil
    end
  rescue HTTParty::Error => e
    puts "Error creating custom field: #{e}"
    nil
  end


# #################################################################################### #
# Usage:
# #################################################################################### #

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
parser = CSVtoCustomFieldParser.new(options[:file])
fields = parser.parse

# Generate field-creator and make consecutive api calls
creator = PagerDutyCustomFieldCreator.new(options[:api_key])
fields.each do |field|
  result = creator.create_custom_field(field)
  if result
    puts "Custom field created: #{field[:name]} with ID: #{result['field']['id']}"
  else
    puts "Failed to create custom field with name: #{field[:name]}"
  end
end
