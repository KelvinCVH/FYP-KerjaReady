import aws_cdk as cdk
from aws_cdk.assertions import Template

from stacks.kerjaready_stack import KerjaReadyStack


def test_every_route_except_health_requires_sign_in():
    app = cdk.App(context={"aws:cdk:bundling-stacks": []})
    stack = KerjaReadyStack(
        app, "TestStack", env=cdk.Environment(account="123456789012", region="ap-southeast-5")
    )
    routes = Template.from_stack(stack).find_resources("AWS::ApiGatewayV2::Route")

    assert routes, "No API routes found"
    for route in routes.values():
        props = route["Properties"]
        if props["RouteKey"] == "GET /health":
            assert props.get("AuthorizationType", "NONE") == "NONE"
        else:
            assert props.get("AuthorizationType") == "JWT", f"{props['RouteKey']} is public"