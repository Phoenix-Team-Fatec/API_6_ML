import argparse
import json

from src.agent.service.change_request_service import ChangeRequestService


def main():
    parser = argparse.ArgumentParser(description="Solicitar alteração de regra no código")
    parser.add_argument("--request", required=True, help="Pedido de alteração")
    parser.add_argument("--apply", action="store_true", help="Aplica a mudança de verdade")
    args = parser.parse_args()

    service = ChangeRequestService()
    result = service.process_change_request(
        user_request=args.request,
        dry_run=not args.apply,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()