import json

def generate_resume_from_template(resume_content, template_choice):
    template_file = f"templates/{template_choice}"
    with open(template_file, "r", encoding="utf-8") as f:
        template = json.load(f)

    # 假设模板文件是JSON格式，其中有一个"sections"字段来放置简历内容
    resume = ""
    for section in template.get("sections", []):
        section_title = section.get("title", "无标题")
        section_content = section.get("content", "无内容")
        resume += f"{section_title}\n{resume_content}\n\n"

    return resume
