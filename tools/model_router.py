try:
    from tools.model_router_core import (
        DEFAULT_ROOT,
        inspect_model_switch_support,
        main,
        recommend_model_profile,
    )
except ModuleNotFoundError:
    from model_router_core import (  # type: ignore
        DEFAULT_ROOT,
        inspect_model_switch_support,
        main,
        recommend_model_profile,
    )


if __name__ == "__main__":
    raise SystemExit(main())
