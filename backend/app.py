from flask import Flask, render_template, request, redirect, session, url_for, jsonify, g, abort
from flask_cors import CORS
from flask import request, session
from datetime import datetime, timedelta
import sqlite3, os

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = "super_secret_key"

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5173"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "project.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user(username):
    conn = get_db()
    user = conn.execute("SELECT username, password FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user

def get_user_full(username):
    conn = get_db()
    user = conn.execute("""
        SELECT username, name, age, experience, post, project, image
        FROM users WHERE username=?
        """, (username,)).fetchone()
    conn.close()
    return user

def get_team_members(project, exclude_username=None):
    conn = get_db()
    c = conn.cursor()
    if exclude_username:
        c.execute("""
            SELECT name FROM users
            WHERE project=? AND username!=?
        """, (project, exclude_username))
    else:
        c.execute("SELECT name FROM users WHERE project=?", (project,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def fetch_leadership():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT username, name, age, experience, post, image
        FROM users
        WHERE post IN ('CHIEF EXECUTIVE OFFICER (CEO)','MANAGER','FOUNDER')
    """)
    rows = c.fetchall()
    conn.close()

    # convert each row to a dict
    return [
        {
            "username": r[0],
            "name": r[1],
            "age": r[2],
            "experience": r[3],
            "post": r[4],
            "image": r[5]
        } for r in rows
    ]


def fetch_employees():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT username, name, age, experience, post, project, image
        FROM users
        WHERE post NOT IN ('CHIEF EXECUTIVE OFFICER (CEO)','MANAGER','FOUNDER')
    """)
    rows = c.fetchall()
    conn.close()

    return [
        {
            "username": r[0],
            "name": r[1],
            "age": r[2],
            "experience": r[3],
            "post": r[4],
            "project": r[5],
            "image": r[6]
        } for r in rows
    ]

def log_action(username, action, page, severity="LOW", status="OPEN"):
    # Auto classify alert type
    if action in ("LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT"):
        alert_type = "AUTH"

    elif action in ("VIEW_TEAMS", "VIEW_PROJECTS", "PROFILE_VIEW", "VIEW_PROJECT"):
        alert_type = "ACTIVITY"

    elif "DENIED" in action:
        alert_type = "SECURITY"
        severity = "HIGH"   # force HIGH for denied

    elif "SCREENSHOT_ATTEMPT" in action:
        alert_type = "SECURITY"
        severity = "CRITICAL"  # force CRITICAL

    else:
        alert_type = "SYSTEM"

    conn = get_db()
    conn.execute("""
        INSERT INTO logs (username, action, page, severity, alert_type, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, action, page, severity, alert_type, status))
    conn.commit()
    conn.close()

def can_view(viewer, target):
    role = viewer[4]
    if role in ("CHIEF EXECUTIVE OFFICER (CEO)", "MANAGER", "FOUNDER"):
        return True
    if viewer[0] == target[0]:
        return True
    if viewer[5] == target[5]:
        return True
    return False

def can_access_project(user, project_key):
    role = user[4]
    if role in ("CHIEF EXECUTIVE OFFICER (CEO)", "MANAGER", "FOUNDER"):
        return True
    return user[5] == project_key

def get_team_members(project, exclude_username=None):
    if not project:
        return []
    conn = get_db()
    if exclude_username:
        rows = conn.execute("SELECT name FROM users WHERE project=? AND username!=?", (project, exclude_username)).fetchall()
    else:
        rows = conn.execute("SELECT name FROM users WHERE project=?", (project,)).fetchall()
    conn.close()
    return [r["name"] for r in rows]

@app.before_request
def load_user():
    g.current_user = None
    if "username" in session:
        g.current_user = get_user_full(session["username"])

@app.context_processor
def inject_user():
    return dict(current_user=g.current_user)

@app.route("/")
def home():
    return render_template("home.html")

failed_attempts={}
blocked_users=set()

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # check if user already blocked
        if username in blocked_users:
            return "You are no longer able to login again. For more information visit SOC office.",403

        user = get_user(username)

        if user and user["password"] == password:

            # reset fail counter
            failed_attempts[username] = 0

            session["username"] = username
            log_action(username,"LOGIN_SUCCESS","login","LOW","CLOSED")

            return redirect(url_for("dashboard"))

        # login failed
        failed_attempts[username] = failed_attempts.get(username, 0) + 1

        if failed_attempts[username] >= 2:
            blocked_users.add(username)
            log_action(username, "ACCOUNT_BLOCKED", "login", "CRITICAL")
            return "You are no longer able to login again. For more information visit SOC office.",403

        log_action(username or "UNKNOWN","LOGIN_FAILED","login","HIGH")
        return "Invalid credentials",401

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    
    return render_template("dashboard.html")

@app.route("/alerts")
def alerts_page():
    
    return render_template("alerts.html")

@app.route("/logout")
def logout():
    if "username" in session:
        log_action(session["username"], "LOGOUT", "logout", "LOW", "CLOSED")
    session.clear()
    return redirect(url_for("login"))

@app.route("/teams")
def teams():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    log_action(username, "VIEW_TEAMS", "teams_page")
    
    return render_template(
        "teams.html",
        leadership=fetch_leadership(),
        employees=fetch_employees()
    )

@app.route("/profile/<username>")
def profile(username):
    if "username" not in session:
        return jsonify({"error": "login_required"}), 401

    viewer = get_user_full(session["username"])
    target = get_user_full(username)

    if not target:
        return jsonify({"error": "not_found"}), 404

    if not can_view(viewer, target):
        log_action(viewer[0], "PROFILE_ACCESS_DENIED",
                   f"profile_{username}", "MEDIUM", "ACCESS")
        return jsonify({"error": "access_denied"}), 403

    team = get_team_members(target[5], exclude_username=target[0])

    log_action(viewer[0], "PROFILE_VIEW",
               f"profile_{username}")

    return jsonify({
        "username": target[0],
        "name": target[1],
        "age": target[2],
        "experience": target[3],
        "post": target[4],
        "project": target[5],
        "image": target[6],
        "team": team
    })


# PROJECTS
@app.route("/projects")
def projects():
    if "username" not in session:
        return redirect(url_for("login"))
    log_action(session["username"],"VIEW_PROJECTS","projects")
    return render_template("projects.html")

@app.route("/projects/<project_code>")
def project_page(project_code):
    if "username" not in session:
        return redirect(url_for("login"))
    user = get_user_full(session["username"])
    allowed_projects = ["hrx","ap7","omega","im3"]
    if project_code not in allowed_projects:
        abort(404)
    if user["post"] not in ("CHIEF EXECUTIVE OFFICER (CEO)","MANAGER","FOUNDER"):
        if user["project"] != project_code and not session.get(f"unlock_{project_code}"):
            log_action(
                user["username"],
                "PROJECT_ACCESS_DENIED",
                f"project_{project_code}",
                "HIGH"
            )
            return render_template("access_denied.html"),403
    log_action(user["username"],"VIEW_PROJECT",project_code)
    return render_template(f"projects/{project_code}.html")

@app.route("/unlock/<project>", methods=["POST"])
def unlock_project(project):
    if "username" not in session:
        return {"error":"login_required"},401
    data = request.json
    entered = data.get("password")
    conn = get_db()
    user = conn.execute("SELECT post, project FROM users WHERE username=?",(session["username"],)).fetchone()
    row = conn.execute("SELECT password FROM projects WHERE name=?",(project,)).fetchone()
    conn.close()
    if not row: return {"error":"invalid_project"},404
    if user["post"] not in ("CHIEF EXECUTIVE OFFICER (CEO)","MANAGER","FOUNDER"):
        if user["project"] != project: return {"error":"access_denied"},403
    if entered != row["password"]: return {"error":"wrong_password"},401
    session[f"unlock_{project}"] = True
    log_action(session["username"],"PROJECT_UNLOCK",project)
    return {"success":True}

# API ROUTES
# =========================
@app.route("/api/logs")
def api_logs():
    
    conn = get_db()
    rows = conn.execute("""
    SELECT id, username, action, page, severity, alert_type, status, timestamp
    FROM logs
    ORDER BY id DESC
    LIMIT 50
""").fetchall()
    conn.close()
    return jsonify([
        {
            "time": r["timestamp"],
            "username": r["username"],
            "action": r["action"],
            "alert_type": r["alert_type"],       # fixed key
            "description": f"{r['username']} performed {r['action']} on {r['page']}",
            "severity": r["severity"],
            "status": r["status"]
        } for r in rows
    ])

@app.route("/api/alerts", methods=["GET","POST"])
def api_alerts():
    
    conn = get_db()
    c = conn.cursor()
    if request.method=="POST":
        data = request.get_json()
        user = data.get("user")
        action = data.get("action")
        severity = data.get("severity","CRITICAL")
        c.execute("""
            INSERT INTO logs (username, action, page, severity, alert_type, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,(user, action, "dashboard", severity, "SECURITY", "OPEN"))
        conn.commit()
        conn.close()
        return jsonify({"success":True})
    c.execute("""
    SELECT id, username, action, page, severity, alert_type, status, timestamp
    FROM logs
    WHERE severity IN ('HIGH','CRITICAL','LOW','MEDIUM')
    ORDER BY timestamp DESC
    LIMIT 50
""")
    rows = c.fetchall()
    conn.close()
    def make_description(row):
        username, action, page = row[1], row[2], row[3]
        desc = {
            "LOGIN_FAILED": f"{username} failed login",
            "PROJECT_ACCESS_DENIED": f"{username} tried unauthorized project {page.replace('project_','')}",
            "PROFILE_ACCESS_DENIED": f"{username} tried unauthorized profile {page.replace('profile_','')}",
            "SCREENSHOT_ATTEMPT": f"{username} attempted screenshot - CRITICAL",
            "MULTI_FAILED_LOGIN": f"{username} exceeded failed login attempts",
            "IDLE_TIMEOUT": f"{username} session idle timeout",
        }
        return desc.get(action,f"{username} did {action} on {page}")
    return jsonify([
        {
            "id": r[0],
            "time": r[7],
            "username": r[1],
            "action": r[2],
            "alert_type": r[5],
            "severity": r[4],
            "status": r[6],
            "description": make_description(r)
        } for r in rows
    ])
@app.route("/risk")
def risk():
    
    return render_template("risk.html")

@app.route("/api/risk")
def api_risk():
    
    # Example risk data
    data = [
        {"id": 1, "risk": "Server Downtime", "severity": "HIGH", "status": "OPEN"},
        {"id": 2, "risk": "Data Breach", "severity": "CRITICAL", "status": "OPEN"},
        {"id": 3, "risk": "Compliance Issue", "severity": "MEDIUM", "status": "CLOSED"}
    ]
    return jsonify(data)


from datetime import datetime, timedelta

@app.route("/api/suspicious-activity", methods=["POST"])
def suspicious_activity():

    if "username" not in session:
        return "", 401

    data = request.get_json()
    activity_type = data.get("type", "UNKNOWN")
    module = data.get("module", "unknown")

    username = session["username"]

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Count recent tab switches in last 1 minute
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM logs
            WHERE username = ?
            AND action = 'TAB_SWITCH'
            AND timestamp >= datetime('now', '-1 minutes')
        """, (username,))
        total_recent = cursor.fetchone()["total"]

        # Escalate severity based on frequency
        if total_recent >= 5:
            severity = "HIGH"
        elif total_recent >= 3:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Log the current event
        cursor.execute("""
            INSERT INTO logs (username, action, module, severity, category, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (username, activity_type, module, severity, "SECURITY"))

        conn.commit()
        return "", 204

    except Exception as e:
        print("ERROR /api/suspicious-activity:", e)
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if conn:
            conn.close()


@app.route("/api/screenshot-attempt", methods=["POST"])
def screenshot_attempt():

    if "username" not in session:
        return "", 401

    data = request.get_json()
    module = data.get("module", "unknown")

    log_action(
        session["username"],
        "SCREENSHOT_ATTEMPT",
        module,
        "CRITICAL",
        "SECURITY"
    )

    return "", 204

@app.route("/response")
def response_dashboard():
   return render_template("response_dashboard.html")

from flask import jsonify
from datetime import datetime
import traceback

@app.route("/api/response-alerts")
def response_alerts():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, action, severity, timestamp
            FROM logs
            ORDER BY timestamp DESC
            LIMIT 50
        """)

        rows = cursor.fetchall()
        response_data = []

        for row in rows:
            log_id = row["id"]
            username = row["username"]
            action = row["action"]
            severity = row["severity"]
            timestamp_str = row["timestamp"]

            # ==================================================
            # 1️⃣ SEVERITY SCORE (Balanced)
            # ==================================================
            severity_weights = {
                "CRITICAL": 80,
                "HIGH": 60,
                "MEDIUM": 40,
                "LOW": 20
            }
            severity_score = severity_weights.get(severity, 30)

            # ==================================================
            # 2️⃣ ACTION SENSITIVITY SCORE
            # ==================================================
            action_risk_map = {
                "DATA_EXPORT_ATTEMPT": 85,
                "MULTIPLE_LOGIN_FAILED": 75,
                "SCREENSHOT_ATTEMPT": 65,
                "FILE_ACCESS_DENIED": 60,
                "LOGIN_FAILED": 50
            }
            sensitivity_score = action_risk_map.get(action, 40)

            # ==================================================
            # 3️⃣ BEHAVIORAL SCORE (User activity intensity)
            # ==================================================
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM logs
                WHERE username = ?
                AND timestamp >= datetime('now', '-10 minutes')
            """, (username,))
            total_recent = cursor.fetchone()["total"]

            if total_recent <= 2:
                behavioral_score = 10
            elif total_recent <= 5:
                behavioral_score = 30
            elif total_recent <= 8:
                behavioral_score = 55
            else:
                behavioral_score = 75

            # ==================================================
            # 4️⃣ CONTEXT SCORE (Time-based anomaly)
            # ==================================================
            context_score = 20
            context_label = "Normal activity window"

            try:
                event_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                hour = event_time.hour

                if 0 <= hour < 5:
                    context_score = 60
                    context_label = "Late-night anomaly"
                elif 22 <= hour < 24:
                    context_score = 40
                    context_label = "After-hours activity"
            except:
                pass

            # ==================================================
            # FINAL WEIGHTED RISK SCORE
            # ==================================================
            risk_score = int(
                (0.35 * severity_score) +
                (0.30 * sensitivity_score) +
                (0.20 * behavioral_score) +
                (0.15 * context_score)
            )

            risk_score = min(risk_score, 100)

            # ==================================================
            # RISK LEVEL CLASSIFICATION
            # ==================================================
            if risk_score >= 75:
                risk_level = "CRITICAL"
            elif risk_score >= 55:
                risk_level = "HIGH"
            elif risk_score >= 35:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            if action == "LOGIN_FAILED" and risk_score >= 35:
                risk_level = "MEDIUM"

            # ==================================================
            # DYNAMIC RECOMMENDATION ENGINE
            # ==================================================
            recommendations = []

            action_recommendations = {
                "DATA_EXPORT_ATTEMPT": [
                    "Audit exported dataset sensitivity",
                    "Verify business justification",
                    "Inspect transfer destination"
                ],
                "MULTIPLE_LOGIN_FAILED": [
                    "Analyze brute-force pattern",
                    "Check IP reputation",
                    "Review authentication logs"
                ],
                "SCREENSHOT_ATTEMPT": [
                    "Review accessed sensitive documents",
                    "Evaluate insider threat indicators",
                    "Restrict screen capture permissions"
                ],
                "FILE_ACCESS_DENIED": [
                    "Audit attempted file path",
                    "Review access control policy",
                    "Check privilege escalation indicators"
                ],
                "LOGIN_FAILED": [
                    "Monitor repeated login attempts",
                    "Validate credential integrity",
                    "Check for password spraying pattern"
                ]
            }

            recommendations.extend(
                action_recommendations.get(
                    action,
                    ["Review event metadata", "Continue monitoring"]
                )
            )

            # Behavioral escalation
            if behavioral_score >= 55:
                recommendations.append("Enable anomaly-based monitoring")

            # Context escalation
            if context_score >= 40:
                recommendations.append("Validate off-hours access approval")

            # Risk-level overlay
            if risk_level == "CRITICAL":
                recommendations.insert(0, "Immediately disable account")
                recommendations.append("Initiate forensic investigation")
                recommendations.append("Escalate to SOC Tier-2")

            elif risk_level == "HIGH":
                recommendations.insert(0, "Temporarily suspend account")
                recommendations.append("Force credential reset")

            elif risk_level == "MEDIUM":
                recommendations.insert(0, "Enforce password reset")

            # Remove duplicates
            recommendations = list(dict.fromkeys(recommendations))

            # ==================================================
            # REASONING BLOCK
            # ==================================================
            reason = (
                f"Composite Model → "
                f"Severity:{severity_score}, "
                f"Sensitivity:{sensitivity_score}, "
                f"Behavior:{behavioral_score}, "
                f"Context:{context_score} ({context_label})."
            )

            impact = (
                f"User '{username}' performed '{action}'. "
                f"Risk classified as {risk_level} based on activity pattern."
            )
            print("DEBUG:", username, action, "Score:", risk_score, "Level:", risk_level)
            response_data.append({
                "id": log_id,
                "username": username,
                "action": action,
                "severity": risk_level,
                "risk_score": risk_score,
                "reason": reason,
                "potential_impact": impact,
                "recommendations": recommendations,
                "time": timestamp_str
            })

        return jsonify(response_data)

    except Exception as e:
        print("ERROR:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if conn:
            conn.close()



import sqlite3
import os
from flask import render_template, send_file
import io
@app.route("/reports")
def reports():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
          SELECT DISTINCT DATE(timestamp), severity
          FROM logs
          WHERE severity IN ('HIGH', 'CRITICAL')
             OR alert_type='UNAUTHORIZED'
         ORDER BY DATE(timestamp) DESC
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template("reports.html", reports=data)


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak
from reportlab.platypus import Preformatted
from reportlab.platypus import Flowable
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.platypus import Frame
from reportlab.platypus import KeepTogether
from reportlab.platypus import Image
from reportlab.platypus import BaseDocTemplate
from reportlab.platypus import FrameBreak
from reportlab.platypus import NextPageTemplate
from reportlab.platypus import PageTemplate
from reportlab.platypus import CondPageBreak
from reportlab.platypus import HRFlowable
from reportlab.platypus import Spacer
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import io


@app.route("/download/<date>/<alert_type>")
def download_report(date, alert_type):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, action, page, severity, alert_type, timestamp
        FROM logs
        WHERE DATE(timestamp)=?
        AND (severity=? OR alert_type=?)
    """, (date, alert_type, alert_type))

    rows = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>SECURITY REPORT</b>", styles['Title']))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Date: {date}", styles['Normal']))
    elements.append(Paragraph(f"Alert Type: {alert_type}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    for row in rows:
        text = f"""
        User: {row[0]}<br/>
        Action: {row[1]}<br/>
        Page: {row[2]}<br/>
        Severity: {row[3]}<br/>
        Alert Type: {row[4]}<br/>
        Time: {row[5]}<br/>
        -----------------------------------------
        """
        elements.append(Paragraph(text, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{date}_{alert_type}_report.pdf",
        mimetype='application/pdf'
    )

from flask import send_from_directory

@app.route("/protected/<project>/<filename>")
def protected_files(project, filename):

    if "username" not in session:
        abort(403)

    user = get_user_full(session["username"])

    # Access control
    if user["post"] not in ("CHIEF EXECUTIVE OFFICER (CEO)", "MANAGER", "FOUNDER"):
        if user["project"] != project and not session.get(f"unlock_{project}"):
            abort(403)

    folder = os.path.join(BASE_DIR, "protected", project)

    return send_from_directory(folder, filename)

# RUN APP
# =========================
if __name__=="__main__":
    app.run(debug=True)