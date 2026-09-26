from src.args import CLIController

def test_cli_parser_arguments():
    controller = CLIController()
    args = controller.parser.parse_args(["--sync", "--dry-run"])
    assert args.sync is True
    assert args.dry_run is True
    assert args.list_movies is False
  
