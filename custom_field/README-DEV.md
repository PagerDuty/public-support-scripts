# Additional Dev. Notes

## Ruby Versioning
- [asdf](https://asdf-vm.com/guide/getting-started.html) is a recommended tool for dealing with ruby version mgmt
  - (getting an installed ruby version to gain precedence over the default mac version can be frustrating)
- If you haven't used asdf at all before you can :
  - `brew install asdf`
  - `source /opt/homebrew/opt/asdf/libexec/asdf.sh`
    - ^ you can add that to your `.zshrc` or just do it manually in a terminal session; it slows down new shell opens otherwise
- Once you've got asdf setup:
  - check current version of ruby specified in `Gemfile` or `Gemfile.lock`
    - you can just use [ripgrep](https://github.com/BurntSushi/ripgrep): `rg ruby --glob 'Gemfile*'`
    - or grep: `grep "ruby " Gemfile*`
  - ```sd
    source /opt/homebrew/opt/asdf/libexec/asdf.sh
    asdf plugin add ruby
    asdf install ruby <version>
    asdf local install ruby <version>
    ```
- then check `ruby --version` to make sure ya got it
  - please feel free to ask questions of your fellower T2ers -- environment setup is much easier in collaboration! :)

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
