require 'dotenv'
require 'rspec'
require_relative 'import_custom_fields'

# NOTE: an api-key is needed for some of these tests
# you can specify it in your shell as part of running the test
# or you can specify it in a local `.env` file
#
# So your test run command will look like the following:
#
# bundle exec rspec spec.rb
# -or-
# TEST_PAGERDUTY_API_KEY='#######' bundle exec rspec spec.rb

# load any local .env files
Dotenv.load
api_key = ENV['TEST_PAGERDUTY_API_KEY']

describe CSVtoCustomFieldParser do
  let(:logger) { Logger.new(STDOUT) }
  let(:csv_file) { 'test.csv' }
  let(:parser) { CSVtoCustomFieldParser.new(csv_file, logger) }

  describe '#parse' do
    it 'parses the CSV file and returns an array of custom fields' do
      fields = parser.parse
      expect(fields).to be_an(Array)
      expect(fields.first).to be_a(Hash)
    end
  end
end

describe PagerDutyCustomFieldCreator do
  let(:logger) { Logger.new(STDOUT) }
  let(:api_token) { api_key }
  let(:creator) { PagerDutyCustomFieldCreator.new(api_token, logger) }

  describe '#create_custom_field' do
    let(:params) do
      {
        'data_type': 'string',
        'name': 'test_name',
        'display_name': 'Test Name',
        'description': 'Test Description',
        'field_type': 'single_value_fixed',
        'field_options': [
          {
            'data' => {
              'data_type' => 'string',
              'value' => 'Option 1'
            }
          },
          {
            'data' => {
              'data_type' => 'string',
              'value' => 'Option 2'
            }
          }
        ]
      }
    end

    it 'creates a custom field and returns the response' do
      response = creator.create_custom_field(params)
      expect(response).to be_a(Hash)
      expect(response['field']).to be_a(Hash)
    end
  end
end
