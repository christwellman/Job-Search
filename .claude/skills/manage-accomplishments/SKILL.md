---
name: manage-accomplishments
description: Add, edit, and organize professional accomplishments for resume tailoring
---

# Manage Accomplishments

Store and organize your key professional achievements, impact stories, and accomplishment narratives. These are automatically matched to job postings and incorporated into tailored resumes.

## Trigger

- User says "add accomplishment" or "add this achievement"
- User says "edit accomplishment [name]" or "remove accomplishment [name]"
- User says "list my accomplishments" or "show accomplishments"
- User wants to review accomplishments before resume tailoring

## Workflow

### Step 1: Capture Accomplishment

When user provides an accomplishment, extract or clarify:
- **Title** - Brief, descriptive name (2-5 words)
- **Impact** - Quantified results with metrics:
  - Numbers: 50%, $200K, 700+, 20+ analyses
  - Scope: organizational reach, number of stakeholders
  - Timeframe: how long it took, how long it lasted
- **Context** - What business problem or opportunity was this?
- **Skills** - Core skills demonstrated (3-5 key skills)
- **Keywords** - ATS-friendly terms relevant to this accomplishment (5-10 keywords)

### Step 2: Validate Completeness

Ensure the accomplishment has:
- ✅ Quantified impact (not vague)
- ✅ Clear business context (not just task description)
- ✅ Relevant skills listed
- ✅ Keywords for job matching
- ✅ Specificity (not inflated claims)

### Step 3: Format Consistently

Use this structure:
```
### Accomplishment: [Title]
**Impact**: [Quantified result with metrics]
**Context**: [What business problem/opportunity?]
**Skills**: [Core skills, comma-separated]
**Keywords**: [ATS-friendly terms, comma-separated]
```

### Step 4: Add to accomplishments.md

Insert into appropriate section:
- **Data Analytics & Leadership**
- **Platform & Infrastructure**
- **Cross-Functional Leadership & Operations**
- **Business Impact & Optimization**
- **Communication & Influence**

Or create new section if needed.

### Step 5: Confirm & Provide Summary

Report:
- Accomplishment added: [Title]
- Section: [Category]
- Keywords for matching: [list]
- Available for resume tailoring: ✅

---

## Best Practices

### Impact Metrics (Use Numbers)
❌ "Improved efficiency"
✅ "Reduced query latency by 60% (2-3 hours → 30 minutes)"

❌ "Led team"
✅ "Directed team of 14 people (6 engineers, 8 developers)"

❌ "Saved money"
✅ "Eliminated $200K+ annual licensing costs; 50% reduction in duplicated data"

### Context (Show Business Problem)
❌ "Built governance framework"
✅ "Rapid data platform growth without proper governance created security/compliance risk; implemented framework ensuring 100% audit compliance"

### Keywords (Natural, Job-Relevant)
✅ Use keywords that match job postings:
- "data governance, compliance, audit-ready" (for governance roles)
- "causal inference, experimentation, statistical rigor" (for analytics roles)
- "operating cadence, QBR, OKR" (for operations roles)
- "cross-functional coordination, change management" (for leadership roles)

### Avoid Keyword Stuffing
❌ "Achieved 50% reduction in latency, improved efficiency, optimized performance, enhanced scalability, modernized architecture"
✅ "Reduced query latency by 60% through Snowflake optimization and ETL redesign"

---

## Editing Accomplishments

### To Update an Accomplishment
```
/manage-accomplishments --edit "Accomplishment Name"
```

Provide new content for:
- Impact (updated metrics?)
- Context (clarification?)
- Skills (additional skills?)
- Keywords (new keywords?)

### To Remove an Accomplishment
```
/manage-accomplishments --remove "Accomplishment Name"
```

### To List All Accomplishments
```
/manage-accomplishments --list
```

---

## Using Accomplishments in Resume Tailoring

### Automatic Matching

When you tailor a resume:
```
/tailor-resume <posting-name>
```

Claude automatically:
1. Analyzes job posting requirements
2. Matches your accomplishments to posting keywords
3. Incorporates most relevant accomplishments into resume bullets
4. Adds metrics and context from accomplishments
5. Uses accomplishment keywords to strengthen keyword matching

### Example Flow

**Job Posting** asks for: "data governance, compliance, enterprise data standards"

**Claude matches** your accomplishments:
- "Built Data Governance & Compliance Framework" ← Perfect match
- Keywords: data governance, compliance, audit-ready, access controls

**Tailored Resume** includes:
- Enhanced bullets emphasizing governance work
- Metrics from accomplishment (700+ ETL jobs, 100% compliance)
- Keywords from accomplishment naturally woven in

---

## Accomplishment Categories

### Data Analytics & Leadership
Accomplishments showing:
- Metrics ownership and definition
- Deep-dive analysis capability
- Statistical rigor and causal inference
- Executive communication
- Team mentorship

Examples:
- "Defined Core Metrics Standard"
- "Led End-to-End Deep-Dive Analysis Program"
- "Set Analytical Standards & Raised Team Performance"

### Platform & Infrastructure
Accomplishments showing:
- Data warehouse/ETL expertise
- Performance optimization
- Technical architecture
- System integration and migration
- Scalability

Examples:
- "Scaled Data Warehouse Architecture"
- "Consolidated Legacy Systems"

### Cross-Functional Leadership & Operations
Accomplishments showing:
- Team leadership
- Operating model design
- Process optimization
- Change management
- Stakeholder coordination

Examples:
- "Directed Multi-Team Operations Function"
- "Built Operating Rhythms & Cadences"

### Business Impact & Optimization
Accomplishments showing:
- ROI and cost savings
- Efficiency improvements
- Financial impact
- Resource optimization
- Technical debt reduction

Examples:
- "Engineered Resource Optimization Model"
- "Implemented PO Forecasting Tool"

### Communication & Influence
Accomplishments showing:
- Data storytelling and translation
- Executive communication
- Influence without authority
- Synthesis and insight generation
- Mentorship

Examples:
- "Translated Complex Analysis into Executive Action"
- "Set Analytical Standards & Raised Team Performance"

---

## Common Mistakes to Avoid

❌ **Generic accomplishments** - "Led cross-functional team"
✅ **Specific accomplishments** - "Led team of 14 (6 engineers, 8 developers) across matrix org; unified siloed operations; improved cross-team communication"

❌ **Unmeasured impact** - "Improved system performance"
✅ **Quantified impact** - "Reduced query latency by 60% (2-3 hours → 30 minutes) through Snowflake optimization"

❌ **Missing context** - "Built governance framework"
✅ **Context included** - "Rapid growth without governance created compliance risk; implemented framework achieving 100% audit compliance"

❌ **Too many accomplishments** - Adds 20 achievements
✅ **Focused list** - Keep 12-15 core accomplishments that cover key domains

❌ **Accomplishments that don't differentiate** - "Used Excel for analysis"
✅ **Accomplishments showing unique value** - "Built predictive model improving resource allocation efficiency by 15%"

---

## How Claude Uses Accomplishments

### During Resume Tailoring

1. **Keyword Extraction**: Pulls keywords from job posting
2. **Accomplishment Matching**: Finds your accomplishments matching keywords
3. **Relevance Ranking**: Orders by importance to specific job
4. **Bullet Integration**: Incorporates accomplishment context into resume bullets
5. **Keyword Reinforcement**: Uses accomplishment keywords throughout resume

### Example

**Job Posting Keywords**: "data governance, metrics definition, compliance, security, cross-functional"

**Claude's Process**:
- ✅ Match: "Built Data Governance & Compliance Framework"
- ✅ Match: "Defined Core Metrics Standard"
- ✅ Match: "Directed Multi-Team Operations Function"
- → Pulls metrics, context, keywords from matches
- → Enhances resume bullets with accomplishment details
- → Increases keyword density naturally

---

## Tips for Best Results

1. **Be specific with metrics** - "50% reduction," not "significant improvement"
2. **Show business impact** - Not just technical accomplishment, but business outcome
3. **Use natural keywords** - Don't keyword-stuff; let keywords flow naturally
4. **Vary your accomplishments** - Cover analytics, operations, leadership, business impact
5. **Update regularly** - Add new accomplishments as you achieve them
6. **Keep them factual** - Only include accomplishments you can defend in interviews

