require 'httparty'
require 'csv'
require 'json'
require 'optparse'

class PagerDutyCustomFieldImporter
  include HTTParty
  base_uri 'https://api.pagerduty.com'
  headers 'Content-Type' => 'application/json'

  attr_reader :api_token

  def initialize(api_token)
    @api_token = api_token
  end

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

  def import_from_csv(csv_file)
    CSV.foreach(csv_file, headers: true) do |row|
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

      result = create_custom_field(params)

      if result
        puts "Custom field created: #{row['name']} with ID: #{result['field']['id']}"
      else
        puts "Failed to create custom field with name: #{row['name']}"
      end
    end
  end

  private

  # for field options if multi or single select
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

  # convert the name into snake case e.g. "test custom field 1" => test_custom_field_1
  def convert_to_snake_case(input)
    input.gsub(' ', '_')
  end
end

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

importer = PagerDutyCustomFieldImporter.new(options[:api_key])
importer.import_from_csv(options[:file])
