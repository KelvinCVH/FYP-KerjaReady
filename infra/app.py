import aws_cdk as cdk
from stacks.kerjaready_stack import KerjaReadyStack
from stacks.kerjaready_ci_stack import KerjaReadyCiStack

app = cdk.App()
env = cdk.Environment(account="063103766930", region="ap-southeast-5")

KerjaReadyStack(app, "KerjaReadyStack", env=env)
KerjaReadyCiStack(app, "KerjaReadyCiStack", env=env)

app.synth()