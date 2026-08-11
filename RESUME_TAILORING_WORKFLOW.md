# Resume Tailoring Workflow

## Overview

This document outlines the complete workflow for tailoring your resume to job postings with ATS-friendly formatting for Workday and other applicant tracking systems.

## Current Status

✅ **Created 5 tailored resumes** (for the 5 job postings you saved):
- Resume_Lead_Data_Analyst_Point.md & .docx
- Resume_Business_Operations_Plaid.md & .docx
- Resume_Senior_Strategic_Insights_Analyst_Calendly.md & .docx
- Resume_Data_Governance_Manager_Headspace.md & .docx
- Resume_Senior_Product_Manager_NVIDIA.md & .docx

Location: `/Users/christwellman/Projects/Job Search/Customized Resumes/`

## How to Use in Future Sessions

### Quick Start: Tailor a single resume

```bash
# Use the tailor-resume skill
/tailor-resume <job-posting-name>
```

Or manually:

1. **Save the job posting** using `/save-posting <url>`
   - This stores posting in `/Postings/` directory
   
2. **Tailor the resume** using `/tailor-resume <posting-name>`
   - Analyzes posting requirements and keywords
   - Customizes resume to highlight matching experience
   - Generates both .md and .docx versions
   - Saves to `Customized Resumes/` directory

### Batch Process: Tailor multiple resumes at once

When you have multiple job postings to apply to:

1. Save all postings first using `/save-posting`
2. Request batch tailoring: "tailor my resume to all saved postings"
3. Review generated resumes in `Customized Resumes/` folder

## ATS Compatibility Checklist

All generated resumes include:

✅ **Format**
- Text-based, no graphics or tables
- Standard section headings (Professional Summary, Work Experience, Education, Skills)
- Clear bullet points

✅ **Formatting**
- Calibri 11pt font (ATS-safe standard)
- Consistent spacing and indentation
- No special characters or formatting codes

✅ **Keywords**
- Extracted from each job posting
- Integrated naturally into bullet points
- Prioritized by relevance

✅ **Content**
- Quantified achievements (metrics, percentages, scale)
- Strong action verbs (lead, drive, own, build, establish)
- Tailored to specific role requirements

## File Formats

### .docx (Word) - Recommended for Workday
- **Use for**: Submitting to Workday and most ATS systems
- **Why**: Better parsing than PDF, cleaner than plain text
- **Format**: Microsoft Word with ATS-friendly styling
- **Location**: `Customized Resumes/Resume_[Role]_[Company].docx`

### .md (Markdown) - For Review & Editing
- **Use for**: Human review, making edits, version control
- **Why**: Plain text, easy to edit, track changes
- **Location**: `Customized Resumes/Resume_[Role]_[Company].md`

## Customization Workflow

### If you need to edit a tailored resume:

1. Open the `.md` version in your text editor
2. Make changes to the markdown file
3. Share the `.md` file with me and say "convert to docx"
4. I'll generate an updated `.docx` version

### If you need to re-tailor a resume:

```bash
/tailor-resume <posting-name> --refresh
```

This will:
- Re-analyze the job posting
- Create a fresh tailored version
- Overwrite previous customized resume
- Generate both .md and .docx

## Best Practices for Workday Submission

1. **Use the .docx version** - it parses better than alternatives
2. **Copy/paste into Workday** if auto-parsing fails (manual entry as fallback)
3. **Keep formatting simple** - don't paste from PDF or fancy designs
4. **Check keywords** - review the tailored version to ensure keywords are natural
5. **Proofread** - verify all information is accurate before submitting

## ATS Scoring Tips

When checking if resume is ready:

- ✅ All keywords from posting appear 1-3 times
- ✅ Professional summary mentions core role requirements
- ✅ Work experience bullets emphasize matching responsibilities
- ✅ Skills section prioritizes tools/technologies from posting
- ✅ No formatting that could confuse parsers (tables, columns, graphics)

## Tools Reference

- **tailor-resume skill**: Main workflow for customizing resumes
- **tailor_resume.py**: Backend script for markdown/docx conversion
- **Customized Resumes/**: Output directory for all tailored resumes
- **Postings/**: Job posting database (stored by save-posting skill)

## Next Steps

1. Open one of the `.docx` resumes in Word to verify formatting looks good
2. Copy the resume content and test it in a Workday application (if available)
3. For each new job posting you want to apply to:
   - Save it with `/save-posting <url>`
   - Tailor resume with `/tailor-resume <posting-name>`
   - Download the `.docx` version and submit to Workday

## Questions & Troubleshooting

**Q: Should I edit the .md or .docx version?**
A: Edit the .md version (easier to track changes), then convert to docx when ready to submit.

**Q: Will Workday parse my .docx resume correctly?**
A: Workday should parse it correctly. If it doesn't, you can manually enter information (Workday will prompt you).

**Q: Can I use these resumes for LinkedIn, Indeed, etc.?**
A: Yes! The resumes are compatible with all major ATS systems. Use the .docx version for best results.

**Q: How often should I update my tailored resumes?**
A: Update whenever you find a new job posting you want to apply to. Use `/tailor-resume <posting-name>` to create a fresh version.
