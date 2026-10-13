# KerjaReady

## Frontend
- Before any frontend work, read and follow `frontend/DESIGN.md`.
- Build UI with the shadcn/ui components in `frontend/src/components/ui/`. Add new ones with `npx shadcn@latest add <name>` from `frontend/`, then restyle them to DESIGN.md.
- Use design tokens (`bg-primary`, `text-muted-foreground`, `border-input`) instead of raw colours where a token exists.
- Icons: `lucide-react` only.
- Pages and components use PascalCase file names, for example `ResumeUploadPage.tsx`.

## Backend and Infrastructure
- Lambda folders use kebab-case (`backend/functions/upload-resume/`), Python files use snake_case (`upload_resume.py`), and AWS resource names use `kerjaready-<kebab-case>`.
- Infrastructure is AWS CDK in Python (`infra/`), region ap-southeast-5. Deploy with `cdk deploy --profile kerjaready`.
- Lambdas reach Aurora through the RDS Data API only. No VPC-attached Lambdas.
- Database changes go in a new numbered, idempotent SQL file in `backend/functions/run-database-migration/migrations/`.