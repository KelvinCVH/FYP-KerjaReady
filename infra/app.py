import aws_cdk as cdk
from stacks.kerjaready_stack import KerjaReadyStack

app = cdk.App()
KerjaReadyStack(
    app,
    "KerjaReadyStack",
    env=cdk.Environment(account="063103766930", region="ap-southeast-5"),
)
app.synth()