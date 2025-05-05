import io
import csv
import json
import math
from datetime import datetime
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.models.feedback import FeedbackAnalysis
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackAnalysisResult
from app.middleware.error import AppError

async def get_sample_feedback() -> bytes:
    """
    Generate a sample CSV template for feedback data
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Header
    writer.writerow([
        "year", "term", "branch", "semester", "subject_code", 
        "subject_name", "faculty_name", "total_responses",
        "q1_score", "q2_score", "q3_score", "q4_score", 
        "q5_score", "q6_score", "q7_score", "q8_score", 
        "q9_score", "q10_score", "q11_score", "q12_score"
    ])
    
    # Sample data
    writer.writerow([
        "2025", "Odd", "CSE", "5", "CS501", 
        "Software Engineering", "Dr. John Doe", "45",
        "4.2", "4.0", "3.8", "4.1", 
        "3.9", "4.3", "3.7", "4.2", 
        "4.5", "4.0", "3.6", "4.4"
    ])
    
    return output.getvalue().encode('utf-8')

async def process_feedback_csv(db: Session, file: UploadFile, background_tasks: Optional[BackgroundTasks] = None) -> str:
    """
    Process uploaded feedback data CSV
    """
    if not file.filename.endswith('.csv'):
        raise AppError(status_code=400, message="File must be a CSV")
    
    content = await file.read()
    
    try:
        rows = content.decode('utf-8').splitlines()
        reader = csv.DictReader(rows)
        
        # Basic validation
        required_columns = [
            "year", "term", "branch", "semester", "subject_code", 
            "subject_name", "faculty_name", "total_responses"
        ]
        
        for column in required_columns:
            if column not in reader.fieldnames:
                raise AppError(status_code=400, message=f"Missing required column: {column}")
        
        # Process records and create feedback analysis entries
        feedback_ids = []
        for record in reader:
            feedback_data = {
                "year": int(record["year"]),
                "term": record["term"],
                "branch": record["branch"],
                "semester": int(record["semester"]),
                "subject_code": record["subject_code"],
                "subject_name": record["subject_name"],
                "faculty_name": record["faculty_name"],
                "total_responses": int(record["total_responses"]),
            }
            
            # Add question scores if present
            for i in range(1, 13):
                q_key = f"q{i}_score"
                if q_key in record:
                    feedback_data[q_key] = float(record[q_key])
            
            # Create feedback analysis record
            feedback_record = FeedbackCreate(**feedback_data)
            feedback_id = await create_feedback(db, feedback_record)
            feedback_ids.append(feedback_id)
            
            # Trigger background analysis if available
            if background_tasks:
                background_tasks.add_task(analyze_feedback_data, db, feedback_id)
        
        return f"Processed {len(feedback_ids)} feedback records"
        
    except Exception as e:
        raise AppError(status_code=500, message=f"Error processing CSV: {str(e)}")

async def create_feedback(db: Session, feedback_data: FeedbackCreate) -> str:
    """
    Create new feedback analysis record
    """
    # Calculate average score
    score_fields = [
        feedback_data.q1_score, feedback_data.q2_score,
        feedback_data.q3_score, feedback_data.q4_score,
        feedback_data.q5_score, feedback_data.q6_score,
        feedback_data.q7_score, feedback_data.q8_score,
        feedback_data.q9_score, feedback_data.q10_score,
        feedback_data.q11_score, feedback_data.q12_score
    ]
    
    avg_score = sum(score_fields) / len(score_fields)
    
    # Create DB model
    db_feedback = FeedbackAnalysis(
        id=str(uuid.uuid4()),
        year=feedback_data.year,
        term=feedback_data.term,
        branch=feedback_data.branch,
        semester=feedback_data.semester,
        subject_code=feedback_data.subject_code,
        subject_name=feedback_data.subject_name,
        faculty_name=feedback_data.faculty_name,
        total_responses=feedback_data.total_responses,
        average_score=avg_score,
        q1_score=feedback_data.q1_score,
        q2_score=feedback_data.q2_score,
        q3_score=feedback_data.q3_score,
        q4_score=feedback_data.q4_score,
        q5_score=feedback_data.q5_score,
        q6_score=feedback_data.q6_score,
        q7_score=feedback_data.q7_score,
        q8_score=feedback_data.q8_score,
        q9_score=feedback_data.q9_score,
        q10_score=feedback_data.q10_score,
        q11_score=feedback_data.q11_score,
        q12_score=feedback_data.q12_score
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback.id

async def analyze_feedback_data(db: Session, feedback_id: str) -> FeedbackAnalysisResult:
    """
    Analyze feedback data and generate insights
    """
    # Get the feedback record
    db_feedback = db.query(FeedbackAnalysis).filter(FeedbackAnalysis.id == feedback_id).first()
    
    if not db_feedback:
        raise AppError(status_code=404, message="Feedback record not found")
    
    # Extract scores for analysis
    scores = [
        db_feedback.q1_score, db_feedback.q2_score,
        db_feedback.q3_score, db_feedback.q4_score,
        db_feedback.q5_score, db_feedback.q6_score,
        db_feedback.q7_score, db_feedback.q8_score,
        db_feedback.q9_score, db_feedback.q10_score,
        db_feedback.q11_score, db_feedback.q12_score
    ]
    
    # Perform analysis
    mean_score = sum(scores) / len(scores)
    median_score = sorted(scores)[len(scores) // 2]
    std_dev = math.sqrt(sum((x - mean_score) ** 2 for x in scores) / len(scores))
    min_score = min(scores)
    max_score = max(scores)
    
    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []
    recommendations = []
    
    for i, score in enumerate(scores):
        q_num = i + 1
        if score >= mean_score + 0.2:
            strengths.append(f"Q{q_num}: {score:.2f}")
        elif score <= mean_score - 0.2:
            weaknesses.append(f"Q{q_num}: {score:.2f}")
    
    # Generate recommendations
    if len(weaknesses) > 0:
        recommendations.append(f"Consider improving in areas: {', '.join(weaknesses)}")
    
    if mean_score < 3.5:
        recommendations.append("Overall feedback score is below average. Consider comprehensive improvement strategies.")
    elif mean_score >= 4.0:
        recommendations.append("Excellent overall feedback. Maintain current teaching methodologies.")
    
    # Prepare statistics
    statistics = {
        "mean": mean_score,
        "median": median_score,
        "std_dev": std_dev,
        "min": min_score,
        "max": max_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "total_responses": db_feedback.total_responses
    }
    
    # Update database with analysis results
    db_feedback.report_data = {
        "statistics": statistics,
        "recommendations": recommendations,
        "analyzed_at": datetime.utcnow().isoformat()
    }
    
    db.commit()
    db.refresh(db_feedback)
    
    return FeedbackAnalysisResult(
        feedback_id=feedback_id,
        statistics=statistics,
        recommendations=recommendations
    )

async def get_feedback_report(db: Session, feedback_id: str) -> Dict[str, Any]:
    """
    Get feedback report by ID
    """
    db_feedback = db.query(FeedbackAnalysis).filter(FeedbackAnalysis.id == feedback_id).first()
    
    if not db_feedback:
        raise AppError(status_code=404, message="Feedback report not found")
    
    # If report data doesn't exist, generate it
    if not db_feedback.report_data:
        await analyze_feedback_data(db, feedback_id)
        db.refresh(db_feedback)
    
    # Convert to dict
    report = {
        "id": db_feedback.id,
        "year": db_feedback.year,
        "term": db_feedback.term,
        "branch": db_feedback.branch,
        "semester": db_feedback.semester,
        "subject_code": db_feedback.subject_code,
        "subject_name": db_feedback.subject_name,
        "faculty_name": db_feedback.faculty_name,
        "total_responses": db_feedback.total_responses,
        "average_score": db_feedback.average_score,
        "scores": {
            "q1": db_feedback.q1_score,
            "q2": db_feedback.q2_score,
            "q3": db_feedback.q3_score,
            "q4": db_feedback.q4_score,
            "q5": db_feedback.q5_score,
            "q6": db_feedback.q6_score,
            "q7": db_feedback.q7_score,
            "q8": db_feedback.q8_score,
            "q9": db_feedback.q9_score,
            "q10": db_feedback.q10_score,
            "q11": db_feedback.q11_score,
            "q12": db_feedback.q12_score
        },
        "report": db_feedback.report_data
    }
    
    return report

async def generate_latex_report(db: Session, feedback_id: str) -> bytes:
    """
    Generate LaTeX report for feedback analysis
    """
    # Get report data
    report = await get_feedback_report(db, feedback_id)
    
    # Build LaTeX document
    latex = []
    latex.append(r"\documentclass{article}")
    latex.append(r"\usepackage{graphicx}")
    latex.append(r"\usepackage{booktabs}")
    latex.append(r"\usepackage{geometry}")
    latex.append(r"\usepackage{pgfplots}")
    latex.append(r"\pgfplotsset{compat=1.17}")
    latex.append(r"\geometry{a4paper, margin=1in}")
    latex.append(r"\title{Faculty Feedback Analysis Report}")
    latex.append(r"\author{GPP Portal Feedback Analysis System}")
    latex.append(r"\date{\today}")
    latex.append(r"\begin{document}")
    latex.append(r"\maketitle")
    
    # Basic information
    latex.append(r"\section{Basic Information}")
    latex.append(r"\begin{tabular}{ll}")
    latex.append(r"Subject Code & " + report["subject_code"] + r" \\")
    latex.append(r"Subject Name & " + report["subject_name"] + r" \\")
    latex.append(r"Faculty Name & " + report["faculty_name"] + r" \\")
    latex.append(r"Academic Year & " + str(report["year"]) + r" \\")
    latex.append(r"Term & " + report["term"] + r" \\")
    latex.append(r"Branch & " + report["branch"] + r" \\")
    latex.append(r"Semester & " + str(report["semester"]) + r" \\")
    latex.append(r"Total Responses & " + str(report["total_responses"]) + r" \\")
    latex.append(r"Average Score & " + f"{report['average_score']:.2f}" + r" \\")
    latex.append(r"\end{tabular}")
    
    # Scores table
    latex.append(r"\section{Question-wise Scores}")
    latex.append(r"\begin{tabular}{ccc}")
    latex.append(r"\toprule")
    latex.append(r"Question & Score & Rating \\")
    latex.append(r"\midrule")
    
    for i in range(1, 13):
        q_key = f"q{i}"
        score = report["scores"][q_key]
        rating = "Excellent" if score >= 4.5 else "Very Good" if score >= 4.0 else "Good" if score >= 3.5 else "Average" if score >= 3.0 else "Needs Improvement"
        latex.append(f"Q{i} & {score:.2f} & {rating} \\\\")
    
    latex.append(r"\bottomrule")
    latex.append(r"\end{tabular}")
    
    # Bar chart
    latex.append(r"\section{Score Visualization}")
    latex.append(r"\begin{tikzpicture}")
    latex.append(r"\begin{axis}[")
    latex.append(r"    ybar,")
    latex.append(r"    bar width=15pt,")
    latex.append(r"    width=\textwidth,")
    latex.append(r"    height=8cm,")
    latex.append(r"    xlabel={Question Number},")
    latex.append(r"    ylabel={Score},")
    latex.append(r"    ymin=0, ymax=5,")
    latex.append(r"    xtick={1,2,3,4,5,6,7,8,9,10,11,12},")
    latex.append(r"    xticklabels={Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10,Q11,Q12},")
    latex.append(r"    nodes near coords,")
    latex.append(r"    nodes near coords align={vertical},")
    latex.append(r"    ]")
    
    scores = []
    for i in range(1, 13):
        scores.append(str(report["scores"][f"q{i}"]))
    
    latex.append(r"    \addplot coordinates {")
    for i in range(1, 13):
        latex.append(f"        ({i}, {scores[i-1]})")
    latex.append(r"    };")
    latex.append(r"\end{axis}")
    latex.append(r"\end{tikzpicture}")
    
    # Analysis
    latex.append(r"\section{Analysis}")
    
    if "report" in report and "statistics" in report["report"]:
        stats = report["report"]["statistics"]
        
        latex.append(r"\subsection{Statistical Analysis}")
        latex.append(r"\begin{tabular}{ll}")
        latex.append(r"Mean Score & " + f"{stats['mean']:.2f}" + r" \\")
        latex.append(r"Median Score & " + f"{stats['median']:.2f}" + r" \\")
        latex.append(r"Standard Deviation & " + f"{stats['std_dev']:.2f}" + r" \\")
        latex.append(r"Minimum Score & " + f"{stats['min']:.2f}" + r" \\")
        latex.append(r"Maximum Score & " + f"{stats['max']:.2f}" + r" \\")
        latex.append(r"\end{tabular}")
        
        # Strengths and weaknesses
        latex.append(r"\subsection{Strengths}")
        if stats['strengths']:
            latex.append(r"\begin{itemize}")
            for strength in stats['strengths']:
                latex.append(r"    \item " + strength)
            latex.append(r"\end{itemize}")
        else:
            latex.append("No significant strengths identified.")
        
        latex.append(r"\subsection{Areas for Improvement}")
        if stats['weaknesses']:
            latex.append(r"\begin{itemize}")
            for weakness in stats['weaknesses']:
                latex.append(r"    \item " + weakness)
            latex.append(r"\end{itemize}")
        else:
            latex.append("No significant weaknesses identified.")
    
    # Recommendations
    if "report" in report and "recommendations" in report["report"]:
        latex.append(r"\section{Recommendations}")
        latex.append(r"\begin{itemize}")
        for rec in report["report"]["recommendations"]:
            latex.append(r"    \item " + rec)
        latex.append(r"\end{itemize}")
    
    latex.append(r"\section{Conclusion}")
    
    avg = report['average_score']
    if avg >= 4.5:
        conclusion = "The faculty has received exceptional feedback and is performing at a very high level."
    elif avg >= 4.0:
        conclusion = "The faculty is performing very well with strong student satisfaction."
    elif avg >= 3.5:
        conclusion = "The faculty is performing adequately but has room for improvement."
    else:
        conclusion = "The faculty needs significant improvement in teaching methodologies."
    
    latex.append(conclusion)
    
    # End document
    latex.append(r"\end{document}")
    
    return "\n".join(latex).encode('utf-8')

async def generate_pdf_report(db: Session, feedback_id: str) -> bytes:
    """
    Generate PDF report for feedback analysis
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        # Fallback to returning LaTeX if WeasyPrint is not available
        return await generate_latex_report(db, feedback_id)
    
    # Get report data
    report = await get_feedback_report(db, feedback_id)
    
    # Build HTML content
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Faculty Feedback Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1, h2, h3 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .chart {{ width: 100%; height: 300px; margin: 20px 0; }}
            .container {{ margin: 20px 0; }}
            .metrics {{ display: flex; flex-wrap: wrap; }}
            .metric-card {{ 
                flex: 1; 
                min-width: 200px; 
                margin: 10px; 
                padding: 15px; 
                border-radius: 5px; 
                background: #f9f9f9; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            }}
            .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
            .metric-label {{ color: #666; }}
            .good {{ color: green; }}
            .average {{ color: orange; }}
            .poor {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Faculty Feedback Analysis Report</h1>
        
        <div class="container">
            <h2>Basic Information</h2>
            <table>
                <tr><th>Subject Code</th><td>{report['subject_code']}</td></tr>
                <tr><th>Subject Name</th><td>{report['subject_name']}</td></tr>
                <tr><th>Faculty Name</th><td>{report['faculty_name']}</td></tr>
                <tr><th>Academic Year</th><td>{report['year']}</td></tr>
                <tr><th>Term</th><td>{report['term']}</td></tr>
                <tr><th>Branch</th><td>{report['branch']}</td></tr>
                <tr><th>Semester</th><td>{report['semester']}</td></tr>
                <tr><th>Total Responses</th><td>{report['total_responses']}</td></tr>
                <tr><th>Average Score</th><td>{report['average_score']:.2f}</td></tr>
            </table>
        </div>
        
        <div class="container">
            <h2>Question-wise Scores</h2>
            <table>
                <tr>
                    <th>Question</th>
                    <th>Score</th>
                    <th>Rating</th>
                </tr>
    """
    
    for i in range(1, 13):
        q_key = f"q{i}"
        score = report["scores"][q_key]
        rating_class = "good" if score >= 4.0 else "average" if score >= 3.0 else "poor"
        rating = "Excellent" if score >= 4.5 else "Very Good" if score >= 4.0 else "Good" if score >= 3.5 else "Average" if score >= 3.0 else "Needs Improvement"
        html += f"""
                <tr>
                    <td>Q{i}</td>
                    <td>{score:.2f}</td>
                    <td class="{rating_class}">{rating}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="container">
            <h2>Analysis</h2>
    """
    
    if "report" in report and "statistics" in report["report"]:
        stats = report["report"]["statistics"]
        
        html += f"""
            <h3>Statistical Analysis</h3>
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Mean Score</div>
                    <div class="metric-value">{stats['mean']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Median Score</div>
                    <div class="metric-value">{stats['median']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Standard Deviation</div>
                    <div class="metric-value">{stats['std_dev']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Min Score</div>
                    <div class="metric-value">{stats['min']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Score</div>
                    <div class="metric-value">{stats['max']:.2f}</div>
                </div>
            </div>
            
            <h3>Strengths</h3>
        """
        
        if stats['strengths']:
            html += "<ul>"
            for strength in stats['strengths']:
                html += f"<li>{strength}</li>"
            html += "</ul>"
        else:
            html += "<p>No significant strengths identified.</p>"
        
        html += "<h3>Areas for Improvement</h3>"
        if stats['weaknesses']:
            html += "<ul>"
            for weakness in stats['weaknesses']:
                html += f"<li>{weakness}</li>"
            html += "</ul>"
        else:
            html += "<p>No significant weaknesses identified.</p>"
    
    # Recommendations
    if "report" in report and "recommendations" in report["report"]:
        html += "<h2>Recommendations</h2><ul>"
        for rec in report["report"]["recommendations"]:
            html += f"<li>{rec}</li>"
        html += "</ul>"
    
    html += "<h2>Conclusion</h2>"
    
    avg = report['average_score']
    conclusion_class = "good" if avg >= 4.0 else "average" if avg >= 3.0 else "poor"
    
    if avg >= 4.5:
        conclusion = "The faculty has received exceptional feedback and is performing at a very high level."
    elif avg >= 4.0:
        conclusion = "The faculty is performing very well with strong student satisfaction."
    elif avg >= 3.5:
        conclusion = "The faculty is performing adequately but has room for improvement."
    else:
        conclusion = "The faculty needs significant improvement in teaching methodologies."
    
    html += f'<p class="{conclusion_class}">{conclusion}</p>'
    html += """
    </body>
    </html>
    """
    
    # Generate PDF
    font_config = FontConfiguration()
    pdf = HTML(string=html).write_pdf(font_config=font_config)
    return pdf

async def generate_feedback_report(db: Session, feedback_id: str) -> bytes:
    """
    Generate and combine feedback reports in multiple formats
    """
    try:
        import zipfile
    except ImportError:
        # Fallback to just returning PDF if zipfile is not available
        return await generate_pdf_report(db, feedback_id)
    
    report = await get_feedback_report(db, feedback_id)
    
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add JSON report
        zf.writestr('feedback_report.json', json.dumps(report, indent=2))
        
        # Add LaTeX report
        latex_content = await generate_latex_report(db, feedback_id)
        zf.writestr('feedback_report.tex', latex_content)
        
        # Add PDF report
        pdf_content = await generate_pdf_report(db, feedback_id)
        zf.writestr('feedback_report.pdf', pdf_content)
        
        # Generate Excel report
        try:
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Basic info sheet
                basic_info = pd.DataFrame({
                    'Property': [
                        'Subject Code', 'Subject Name', 'Faculty Name',
                        'Academic Year', 'Term', 'Branch', 'Semester',
                        'Total Responses', 'Average Score'
                    ],
                    'Value': [
                        report['subject_code'], report['subject_name'], 
                        report['faculty_name'], report['year'], report['term'],
                        report['branch'], report['semester'],
                        report['total_responses'], f"{report['average_score']:.2f}"
                    ]
                })
                basic_info.to_excel(writer, sheet_name='Basic Info', index=False)
                
                # Scores sheet
                scores_data = {
                    'Question': [f'Q{i}' for i in range(1, 13)],
                    'Score': [report['scores'][f'q{i}'] for i in range(1, 13)]
                }
                
                scores_df = pd.DataFrame(scores_data)
                scores_df.to_excel(writer, sheet_name='Scores', index=False)
                
                # Analysis sheet if available
                if "report" in report and "statistics" in report["report"]:
                    stats = report["report"]["statistics"]
                    analysis_data = {
                        'Metric': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                        'Value': [
                            stats['mean'], stats['median'], 
                            stats['std_dev'], stats['min'], stats['max']
                        ]
                    }
                    analysis_df = pd.DataFrame(analysis_data)
                    analysis_df.to_excel(writer, sheet_name='Analysis', index=False)
                    
                # Recommendations sheet if available
                if "report" in report and "recommendations" in report["report"]:
                    rec_data = {
                        'Recommendations': report["report"]["recommendations"]
                    }
                    rec_df = pd.DataFrame(rec_data)
                    rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
            
            excel_content = excel_buffer.getvalue()
            zf.writestr('feedback_report.xlsx', excel_content)
        
        except Exception:
            # Skip Excel if there's an issue
            pass
    
    buffer.seek(0)
    return buffer.getvalue()