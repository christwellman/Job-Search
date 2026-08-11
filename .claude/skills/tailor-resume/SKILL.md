---
name: tailor-resume
description: Tailor resume to job posting(s) with ATS-friendly formatting for Workday compatibility
---

# Tailor Resume

Customize resume to match specific job posting(s), extracting key requirements and keywords, then generate ATS-friendly versions in both Markdown and Word format.

## Trigger

- User says "tailor my resume to [posting name]" or "customize resume for [role]"
- User provides job posting URL or file path
- User wants to update existing tailored resume

## Workflow

### Step 1: Identify the job posting
- Check `/Users/christwellman/Projects/Job Search/Postings/` for matching posting file
- If posting not found, ask user to save it first using `/save-posting`
- Extract: title, company, location, requirements, key keywords, responsibilities

### Step 2: Analyze role requirements & match accomplishments
Extract and categorize:
- **Core skills** (required technical/functional skills)
- **Experience level** (years, specific domain)
- **Keywords** (both hard skills and soft skills from job description)
- **Key responsibilities** (what day-to-day work looks like)
- **Company context** (industry, stage, culture signals)

**NEW**: Match job posting keywords to accomplishments:
- Read `/Users/christwellman/Projects/Job Search/accomplishments.md`
- Identify which accomplishments match posting keywords
- Rank by relevance to this specific role
- Pull metrics, context, and keywords from matches

### Step 3: Customize resume with accomplishment insights
Using Chris's base resume (`/Users/christwellman/Projects/Job Search/Resume.md`), tailor by:
1. **Professional Summary** - Rewrite to match role focus and key requirements; incorporate impact language from matched accomplishments
2. **Work Experience** - Reorder roles by relevance; modify bullet points to:
   - Use keywords from job description AND matched accomplishments
   - Emphasize matching responsibilities and achievements
   - Incorporate quantified metrics from accomplishments (e.g., "50% reduction," "700+ daily ETL jobs," "100% compliance")
   - Use accomplishment context to strengthen bullets
   - Use strong action verbs aligned with role
3. **Skills Section** - Prioritize skills matching job posting; integrate keywords from matched accomplishments
4. **Education** - Keep as-is (typically unchanged)

**Example**: Job posting needs "data governance"
- Match accomplishment: "Built Data Governance & Compliance Framework"
- Enhance resume with: accomplishment metrics (700+ ETL jobs, 100% compliance), context (security/compliance risk), keywords (governance, audit-ready, access controls)
- Result: More relevant, more specific, higher keyword density

### Step 3b: Incorporate accomplishment narratives
For each matched accomplishment:
- Extract quantified **impact** (metrics, scale, timeframe)
- Extract **context** (business problem solved)
- Extract **keywords** (for reinforcement)
- Weave into relevant resume bullets
- Maintain natural language (no keyword stuffing)

This step ensures your resume includes:
- ✅ Specific metrics that prove impact
- ✅ Business context that explains relevance
- ✅ Job-matching keywords naturally woven in
- ✅ Coherent narrative connecting accomplishments to role

### Step 4: Format for ATS
Ensure compliance with Workday parsing requirements:
- ✅ Clean text-based format
- ✅ Standard section headings (Professional Summary, Work Experience, Education, Skills & Certifications)
- ✅ Clear bullet points (no fancy formatting)
- ✅ No tables, graphics, or special characters
- ✅ Consistent font and spacing
- ✅ Keywords distributed naturally throughout

### Step 5: Generate outputs
1. Save Markdown (.md) version for human review/editing
2. Save Word (.docx) version for Workday submission
   - Use Calibri 11pt font (standard, ATS-safe)
   - Proper spacing and section breaks
   - Center name/header, left-align body text

**Output location:** `/Users/christwellman/Projects/Job Search/Customized Resumes/Resume_[Role]_[Company].md` and `.docx`

### Step 6: Provide summary
Report:
- Resume created for [Job Title] at [Company]
- Key customizations made (which sections/keywords updated)
- ATS compatibility status
- File paths for both .md and .docx versions

## Best Practices

- **Accomplishment integration**: Automatically match job posting keywords to accomplishments; pull metrics and context from matches
- **Keyword strategy**: Use keywords naturally within bullet points; don't keyword-stuff; accomplish this by weaving in keywords from matched accomplishments
- **Quantification**: Include metrics from accomplishments (%, $, time savings, scale); accomplishments provide pre-validated impact numbers
- **Action verbs**: Lead, drive, own, build, establish, implement, architect; use verbs from accomplishment descriptions
- **Specificity**: Tailor to the exact role using matched accomplishments; different jobs will highlight different accomplishments
- **Length**: 1 page for early career, 1-2 pages for mid/senior roles (Chris has 15 years → 1-2 pages OK)
- **Business context**: Use accomplishment context to explain WHY things matter, not just WHAT was done

## Keywords to prioritize

When tailoring, look for and include:
- **Technical tools**: SQL, Python, Tableau, Snowflake, etc.
- **Methodologies**: Agile, experimentation, causal inference, etc.
- **Business terms**: OKRs, QBRs, GTM, product strategy, etc.
- **Soft skills**: Communication, cross-functional, leadership, etc.

## Common mistakes to avoid

- ❌ Over-formatting (tables, columns, graphics) → breaks ATS parsing
- ❌ Keyword stuffing → reads as unnatural, hurts human reader
- ❌ Generic bullets → doesn't show relevance to specific role
- ❌ Missing metrics → shows impact less clearly
- ❌ Inconsistent section headings → confuses ATS

## ATS Compatibility

Both `.md` and `.docx` versions are:
- Parseable by Workday, LinkedIn, Indeed, and other major ATS systems
- Readable by humans (hiring managers, recruiters)
- Ready for manual data entry into Workday if needed (though parsing should work)

**Recommendation**: Submit `.docx` version to Workday (better parsing than PDFs, cleaner than plain text)
