CREATE EXTENSION IF NOT EXISTS vector;

-------------
--- ACCOUNT
-------------

-- User table: Platform account for a candidate/recruiters, linked to Cognito user
CREATE TABLE IF NOT EXISTS users(
    user_id uuid PRIMARY KEY,
    email varchar(255) NOT NULL UNIQUE,
    full_name varchar(100) NOT NULL,
    account_type varchar(10) NOT NULL CHECK (account_type IN ('candidate', 'recruiter')),
    company_name varchar(150),
    CHECK (account_type = 'recruiter' OR company_name IS NULL)
);
COMMENT ON TABLE users IS 'Platform account for a candidate/recruiters, linked to Cognito user';

------------------
--- KNOWLEDGE BASE
-------------------

-- role table: Target technology roles covered by the knowledge base
CREATE TABLE IF NOT EXISTS roles(
    role_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title varchar(100) NOT NULL UNIQUE
);
COMMENT ON TABLE roles IS 'Target technology roles covered by the knowledge base';

-- skills table: Normalised skill vocabulary
CREATE TABLE IF NOT EXISTS skills(
    skill_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name varchar(150) NOT NULL UNIQUE
);
COMMENT ON TABLE skills IS 'Normalised skill vocabulary';

-- role_skills table: Skills required by each role where they are derived from Malaysian job postings
CREATE TABLE IF NOT EXISTS role_skills(
    role_id bigint NOT NULL REFERENCES roles (role_id) ON DELETE CASCADE,
    skill_id bigint NOT NULL REFERENCES skills (skill_id),
    demand_share numeric(5,4) NOT NULL CHECK (demand_share > 0 AND demand_share <=1),
    PRIMARY KEY (role_id, skill_id) 
);
COMMENT ON TABLE role_skills IS 'Skills required by each role where they are derived from Malaysian job postings';

-- job_postings table: Malaysian ICT job postings from the source dataset
CREATE TABLE IF NOT EXISTS job_postings(
    posting_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id bigint NOT NULL REFERENCES roles (role_id) ON DELETE CASCADE,
    job_title varchar(200) NOT NULL,
    posted_date date
);
COMMENT ON TABLE job_postings IS 'Malaysian ICT job postings from the source dataset';
CREATE INDEX IF NOT EXISTS job_postings_role_id_index ON job_postings (role_id);

-- posting_chunks table: Section-level chunks for job postings with embeddings for retrieval
CREATE TABLE IF NOT EXISTS posting_chunks(
    chunk_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    posting_id bigint NOT NULL REFERENCES job_postings (posting_id) ON DELETE CASCADE,
    section_name varchar(50) NOT NULL,
    chunk_text text NOT NULL,
    embedding vector(1024) NOT NULL
);
COMMENT ON TABLE posting_chunks IS 'Section-level chunks for job postings with embeddings for retrieval';
CREATE INDEX IF NOT EXISTS posting_chunks_posting_id_index ON posting_chunks (posting_id);
CREATE INDEX IF NOT EXISTS posting_chunks_embedding_hnsw_index ON posting_chunks USING hnsw (embedding vector_cosine_ops);

--------------------------
--- RESUME AND ASSESSMENT
--------------------------

-- resume table: Resume uploaded by candidate and its extracted text
CREATE TABLE IF NOT EXISTS resumes(
    resume_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    candidate_id uuid NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    file_name varchar(255) NOT NULL,
    s3_key varchar(500) NOT NULL UNIQUE,
    extracted_text text NOT NULL,
    uploaded_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE resumes IS 'Resume uploaded by candidate and its extracted text';
CREATE INDEX IF NOT EXISTS resumes_candidate_id_index ON resumes (candidate_id);

-- resume_skills table: Skills evidenced in a resume with the text that evidences each one
CREATE TABLE IF NOT EXISTS resume_skills(
    resume_id bigint NOT NULL REFERENCES resumes (resume_id) ON DELETE CASCADE,
    skill_id bigint NOT NULL REFERENCES skills (skill_id),
    evidence_excerpt text NOT NULL,
    PRIMARY KEY (resume_id, skill_id)
);
COMMENT ON TABLE resume_skills IS 'Skills evidenced in a resume with the text that evidences each one';

-- assessment table: Resume assessment against a selected target role
CREATE TABLE IF NOT EXISTS assessments(
    assessment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resume_id bigint NOT NULL REFERENCES resumes (resume_id) ON DELETE CASCADE,
    role_id bigint NOT NULL REFERENCES roles (role_id),
    content_score numeric(5,2) NOT NULL,
    structure_score numeric(5,2) NOT NULL,
    model_version varchar(50) NOT NULL,
    assessed_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE assessments IS 'Resume assessment against a selected target role';
CREATE INDEX IF NOT EXISTS assessments_resume_id_index ON assessments (resume_id);

-- recommendation table: Resume improvement recommendations for an assessment
CREATE TABLE IF NOT EXISTS recommendations(
    recommendation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assessment_id bigint NOT NULL REFERENCES assessments (assessment_id) ON DELETE CASCADE,
    resume_excerpt text NOT NULL,
    recommendation_text text NOT NULL
);
COMMENT ON TABLE recommendations IS 'Resume improvement recommendations for an assessment';
CREATE INDEX IF NOT EXISTS recommendations_assessment_id_index ON recommendations (assessment_id);

-- roadmap_steps: Ordered learning roadmap for skills not evidenced in the resume
CREATE TABLE IF NOT EXISTS roadmap_steps(
    assessment_id bigint NOT NULL REFERENCES assessments (assessment_id) ON DELETE CASCADE,
    skill_id bigint NOT NULL REFERENCES skills (skill_id),
    step_order smallint NOT NULL CHECK (step_order > 0),
    guidance_text text NOT NULL,
    PRIMARY KEY (assessment_id, skill_id),
    UNIQUE (assessment_id, step_order)
);
COMMENT ON TABLE roadmap_steps IS 'Ordered learning roadmap for skills not evidenced in the resume';

--------------------------
--- RECRUITMENT
--------------------------

-- job_listings table: Job vacancies posted by recruiters
CREATE TABLE IF NOT EXISTS job_listings(
    listing_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recruiter_id uuid NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    title varchar(200) NOT NULL,
    description text NOT NULL,
    location varchar(100) NOT NULL,
    status varchar(10) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    created_at timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE job_listings IS 'Job vacancies posted by recruiters';
CREATE INDEX IF NOT EXISTS job_listings_recruiter_id_index ON job_listings (recruiter_id);

-- listing_skills table: Skills required by a job listing, extracted once when the listing is saved
CREATE TABLE IF NOT EXISTS listing_skills(
    listing_id bigint NOT NULL REFERENCES job_listings (listing_id) ON DELETE CASCADE,
    skill_id bigint NOT NULL REFERENCES skills (skill_id),
    PRIMARY KEY (listing_id, skill_id)
);
COMMENT ON TABLE listing_skills IS 'Skills required by a job listing, extracted once when the listing is saved';

-- match_results table: Match score between a resume and a listing, shown to both candidate and recruiter
CREATE TABLE IF NOT EXISTS match_results(
    resume_id bigint NOT NULL REFERENCES resumes (resume_id) ON DELETE CASCADE,
    listing_id bigint NOT NULL REFERENCES job_listings (listing_id) ON DELETE CASCADE,
    match_score numeric(5,2) NOT NULL,
    matched_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (resume_id, listing_id)
);
COMMENT ON TABLE match_results IS 'Match score between a resume and a listing, shown to both candidate and recruiter';
CREATE INDEX IF NOT EXISTS match_results_listing_id_index ON match_results (listing_id);

-- applications table: Candidate applications and recruiter decisions
CREATE TABLE IF NOT EXISTS applications(
    application_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    listing_id bigint NOT NULL REFERENCES job_listings (listing_id) ON DELETE CASCADE,
    resume_id bigint NOT NULL REFERENCES resumes (resume_id) ON DELETE CASCADE,
    status varchar(10) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'accepted', 'rejected')),
    decision_reason text,
    applied_at timestamptz NOT NULL DEFAULT now(),
    decided_at timestamptz,
    UNIQUE (listing_id, resume_id)
);
COMMENT ON TABLE applications IS 'Candidate applications and recruiter decisions';
CREATE INDEX IF NOT EXISTS applications_resume_id_index ON applications (resume_id);