# Additional Dev. Notes

## API-Key Usage
- The script and tests take the key as an environment variable.  You can pass that in two ways:
  - Directly, prepended to your command as:
    - `PAGERDUTY_API_KEY='#######'`
    - `TEST_RSPEC_PAGERDUTY_API_KEY='#######'`
  - Via a local `.env` file. An example file is provided.
    - `cp fake.env .env; vim .env`

## Set-Up and Teardown
### Custom Field Cruft
- This script does NOT delete custom fields.  It only adds them.  A buffer against well intentioned disruption of a production environment.
  - Manual deletion can be done, with elaborated confirmation step, at: **https://<domain-name>.com/customfields/**
- Set-Up: before any testing run you'll want to ensure that you don't *already* have custom field names matching those you're about to create.
- Teardown: you'll need to clean up after testing the scripts (or just get an accumulation of oddly named custom fields)
- Thanks as always to our testers!

### Installation
- You'll need ruby, of course.  Dependencies should mostly handle themselves, but take a look at the `Gemfile` and `Gemfile.lock` if you're having dependency version issues
- Local Install command: `bundle install --path vendor/bundle`

## General Testing
- Make a csv with whatever you want.  Please do *NOT* use the `rspec_test.csv` or `example.csv`.  But please *do* use them as a base to mutate.
  - `cp example.csv manual_test.csv; vim manual_test.csv` <-- Again, please mutate the files when testing.
- Manual test: `bundle exec ruby import_custom_fields.rb --file manual_test.csv`
- Check logs: `cat application.log`
- Check your instance for changes: **https://<your-domain>.pagerduty.com/customfields/**
 

## Running `rspec` Tests
- Run tests: `bundle exec rspec spec.rb`
- Check your instance for changes: **https://<your-domain>.pagerduty.com/customfields/**
  - note: only one custom field should be written (*not* the entire contents of `rspec_test.csv`)
