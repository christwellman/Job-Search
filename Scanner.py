import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the .env file
env_path = os.path.join(script_dir, '.env')

# Load environment variables from the specified path
load_dotenv(env_path)

# Validate environment variables
required_env_vars = ["OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_PROJECT_ID"]
for var in required_env_vars:
    if not os.getenv(var):
        logging.error(f"Missing environment variable: {var}")
        exit(1)

# Set up OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")
)
PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")

def summarize_job_posting(content):
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Ensure this is the correct model name
            messages=[
                {"role": "system", "content": "You are a career placement specialist, expierenced in finding great job opportunities for skilled individuals."},
                {"role": "user", "content": f"Your task is to analyze the following job posting and provide a concise, easily scannable summary. <Task Breakdown> 1) Extract and list the exact job title. 2) Extract and list the company name.3) Extract and list the job location (or specify \"remote\" if applicable). 4)Identify and list 3-5 key responsibilities of the role. 5) Identify and list the required qualifications and experience. 6) Highlight 1-2 unique or compelling aspects of the role or company. 7) Ensure the summary is focused on the most important and relevant details, formatted as bullet points.:\n\n{content}"}
            ],
            user=PROJECT_ID  # This tags the request with your project identifier
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error summarizing job posting: {e}")
        return None

def tailor_resume(resume_content, job_posting_content):
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Ensure this is the correct model name
        # You are a professional resume writer and career coach with deep knowledge of [position or field, ie software engineering]. Create the most ideal [experience section/resume] that includes this experience [list your experience]. Use your expert knowledge and these keywords [ list the ones you’ve found - check the last video in this series] to optimize it to stand out to hiring managers and recruiters for roles like this: [list roles OR copy and paste a real job description]. Be sure to prioritize my transferable skills in areas I lack experience.
            messages=[
                {"role": "system", "content": "You are a professional resume writer and career coach with deep knowledge of the technology industry, experienced in crafting standout resumes that get past ATS and catch the attention of hiring managers."},
                {"role": "user" ,"content": f"<Instruction>: Please act as an experienced resume editor and recruiter. Your task is to review and enhance my resume based on the job posting provided. Follow the detailed instructions below to ensure a comprehensive and effective revision. \n <Task Breakdown>: \1) Revise my resume and position my experience as a solution to the target job posting's pain points. 2) Tailor each bullet point to reflect the required experience and qualifications specified in the job posting, using similar language. 3) Keep it concise, avoid redundancy and cliché terms, and use active voice. 4) Highlight accomplishments and quantify where possible. 5)Include keywords from the job posting. 6) Prioritize transferable skills in areas where I lack experience. 7) Do not fabricate achievements or skills not present in the original resume 8) Do not alter job titles or employment dates from the original resume. 9) Ensure the output is in Markdown format. 10) Identify and correct any grammatical, spelling, or syntax errors. 11) Highlight formatting issues and suggest changes to improve clarity and effectiveness. 12) Optimize for ATS software. 13) Provide feedback on the content, including its clarity, logical flow, and effectiveness in communicating my background and skills. 14) Suggest improvements to the overall structure and organization of the resume. 15) Focus on best practices and industry standards for resume writing without including personal opinions or preferences. \n <Input Data>:\n<Resume:>\n{resume_content}\n\n<Job Posting:>\n{job_posting_content}"}
            ],
            user=PROJECT_ID  # This tags the request with your project identifier
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error tailoring resume: {e}")
        return None

def process_job_postings(input_folder, output_folder, resume_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    processed_files = set(f[8:] for f in os.listdir(output_folder) if f.startswith("summary_"))

    with open(resume_path, 'r') as resume_file:
        resume_content = resume_file.read()

    if not resume_content.strip():
        logging.error("Resume content is empty.")
        return

    for filename in os.listdir(input_folder):
        if filename.endswith(".txt") and filename not in processed_files:
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"summary_{filename}")
            tailored_resume_path = os.path.join(output_folder, f"Chris Twellman - {filename.replace('.txt', '.md')}")

            try:
                with open(input_path, 'r') as input_file:
                    job_posting_content = input_file.read()

                if not job_posting_content.strip():
                    logging.warning(f"Job posting content is empty for file: {filename}")
                    continue

                summary = summarize_job_posting(job_posting_content)

                if summary:
                    with open(output_path, 'w') as output_file:
                        output_file.write(summary)

                    logging.info(f"Processed: {filename}")

                    tailored_resume = tailor_resume(resume_content, job_posting_content)

                    if tailored_resume:
                        with open(tailored_resume_path, 'w') as tailored_resume_file:
                            tailored_resume_file.write(tailored_resume)

                        logging.info(f"Tailored resume created for: {filename}")
                    else:
                        logging.warning(f"Skipped (tailoring failed): {filename}")
                else:
                    logging.warning(f"Skipped (summary failed): {filename}")
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
        elif filename in processed_files:
            logging.info(f"Skipped (already processed): {filename}")

if __name__ == "__main__":
    input_folder = "Postings"
    # output_folder = "Summaries"
    output_folder = "Customized Resumes"
    resume_path = "/Users/christwellman/Projects/Job Search/Resume.md"  # Path to your resume file in Markdown format
    process_job_postings(input_folder, output_folder, resume_path)