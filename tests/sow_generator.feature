Feature: Generate a scope of work document
  The generator should create a Markdown SOW from a YAML configuration file.

  Scenario: Generate a SOW from the sample configuration
    Given the sample configuration file
    When I generate the scope of work
    Then the command succeeds
    And the output file contains a table of contents
    And the output file contains the project title
    And the output file contains YAML-driven methodology content
    And the output file contains a Gherkin scenario
    And the output file contains the total estimated cost

  Scenario: Reject an invalid configuration
    Given an invalid configuration file
    When I generate the scope of work with the invalid configuration
    Then the command fails
    And the error mentions the invalid configuration

  Scenario: Generate a PDF from a Markdown file
    Given a markdown file for PDF conversion
    When I generate the PDF document
    Then the PDF command succeeds
    And the generated file is a PDF

  Scenario: Reject a missing Markdown file for PDF conversion
    Given a missing markdown file for PDF conversion
    When I generate the PDF document
    Then the PDF command fails
    And the PDF error mentions the missing input file

  Scenario: Generate all demo markdown and PDF files from the demos folder structure
    Given demo directories with multiple YAML files and stale outputs
    When I generate the demo documents with clean mode
    Then the demo document command succeeds
    And the demo markdown files are created for each YAML file
    And the demo PDF files are created for each YAML file
    And stale demo outputs are removed
