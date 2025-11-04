#!/usr/bin/env python3
"""
Results Sharing Module
Compartilha resultados via email, upload, etc
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import argparse
import json


class ResultsSharer:
    """Compartilha resultados de scan"""
    
    def __init__(self, scan_dir: str):
        self.scan_dir = Path(scan_dir)
        
    def send_email(self, 
                   smtp_server: str,
                   smtp_port: int,
                   sender_email: str,
                   sender_password: str,
                   recipient_emails: list,
                   subject: str = None):
        """
        Sends report por email
        """
        
        if not subject:
            subject = f"Jenkins Scan Report - {self.scan_dir.name}"
        
        # Creates mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = subject
        
        # Corpo do email
        html_report = self.scan_dir / "reports" / "report.html"
        summary_file = self.scan_dir / "reports" / "summary.txt"
        
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = f.read()
        else:
            summary = f"Jenkins Scan Results\nScan Directory: {self.scan_dir}"
        
        body = f"""
Hello,

Segue em attachment o report do scan Jenkins.

{summary}

Attached files:
- report.html: Report interativo HTML
- jobs_parameters.csv: Dados em CSV
- complete_scan.json: Dados completos em JSON

Best regards,
Jenkins Scanner
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Anexa files
        files_to_attach = [
            self.scan_dir / "reports" / "report.html",
            self.scan_dir / "exports" / "jobs_parameters.csv",
            self.scan_dir / "exports" / "complete_scan.json",
            self.scan_dir / "reports" / "summary.txt"
        ]
        
        for file_path in files_to_attach:
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 
                                  f'attachment; filename={file_path.name}')
                    msg.attach(part)
        
        # Sends
        try:
            print(f"📧 Sending email to: {', '.join(recipient_emails)}")
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print("✓ Email sent successfully!")
            return True
        except Exception as e:
            print(f"✗ Error ao enviar email: {str(e)}")
            return False
    
    def generate_share_links(self):
        """
        Generates comandos para compartilhar resultados
        """
        print("\n" + "=" * 80)
        print("📤 COMPARTILHAR RESULTADOS")
        print("=" * 80)
        
        html_report = self.scan_dir / "reports" / "report.html"
        csv_export = self.scan_dir / "exports" / "jobs_parameters.csv"
        
        print(f"\n📁 Directory: {self.scan_dir}")
        print(f"\n🌐 To view the HTML report:")
        print(f"   file://{html_report.absolute()}")
        
        print(f"\n📊 Para abrir o CSV no Excel/Google Sheets:")
        print(f"   {csv_export.absolute()}")
        
        print(f"\n📦 Para criar ZIP e compartilhar:")
        print(f"   cd {self.scan_dir.parent}")
        print(f"   zip -r {self.scan_dir.name}.zip {self.scan_dir.name}/")
        
        print(f"\n☁️  Para upload ao S3 (se configurado):")
        print(f"   aws s3 cp {self.scan_dir} s3://meu-bucket/jenkins-scans/ --recursive")
        
        print(f"\n🔗 To share via temporary HTTP server:")
        print(f"   cd {self.scan_dir / 'reports'}")
        print(f"   python3 -m http.server 8000")
        print(f"   # Acesse: http://localhost:8000/report.html")
        
        print("\n" + "=" * 80)
    
    def create_shareable_package(self, output_name: str = None):
        """
        Creates pacote ZIP compartilhável
        """
        import zipfile
        
        if not output_name:
            output_name = f"{self.scan_dir.name}.zip"
        
        output_path = self.scan_dir.parent / output_name
        
        print(f"\n📦 Creating shareable package...")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Adds reports
            for file_path in (self.scan_dir / "reports").rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.scan_dir.parent)
                    zipf.write(file_path, arcname)
            
            # Adds exports
            for file_path in (self.scan_dir / "exports").rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.scan_dir.parent)
                    zipf.write(file_path, arcname)
            
            # Adds configs (sample - primeiros 10)
            config_files = list((self.scan_dir / "configs").glob("*.xml"))[:10]
            for file_path in config_files:
                arcname = file_path.relative_to(self.scan_dir.parent)
                zipf.write(file_path, arcname)
            
            if len(config_files) < len(list((self.scan_dir / "configs").glob("*.xml"))):
                # Creates file README
                readme_content = f"""
Configs Directory
=================

Este ZIP contém apenas os primeiros 10 files de configuration como exemplo.
Para acessar todas as configurations, veja o directory completo:
{self.scan_dir / 'configs'}

Total configs: {len(list((self.scan_dir / 'configs').glob('*.xml')))}
                """
                zipf.writestr(f"{self.scan_dir.name}/configs/README.txt", readme_content)
        
        print(f"✓ Package created: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Compartilha resultados do Jenkins scan',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Generates comandos para compartilhar
  python share_results.py --scan-dir jenkins_scan_results/20241030_120000

  # Creates ZIP compartilhável
  python share_results.py --scan-dir jenkins_scan_results/20241030_120000 --create-zip

  # Sends por email
  python share_results.py --scan-dir jenkins_scan_results/20241030_120000 \\
      --email \\
      --smtp-server smtp.gmail.com \\
      --smtp-port 587 \\
      --sender email@empresa.com \\
      --sender-password "senha" \\
      --recipients destinatario1@empresa.com destinatario2@empresa.com
        """
    )
    
    parser.add_argument('--scan-dir', required=True, 
                       help='Directory do scan')
    parser.add_argument('--create-zip', action='store_true',
                       help='Creates ZIP compartilhável')
    parser.add_argument('--email', action='store_true',
                       help='Sends por email')
    parser.add_argument('--smtp-server', help='Servidor SMTP')
    parser.add_argument('--smtp-port', type=int, default=587, help='Porta SMTP')
    parser.add_argument('--sender', help='Email do sender')
    parser.add_argument('--sender-password', help='Senha do sender')
    parser.add_argument('--recipients', nargs='+', help='Emails recipients')
    parser.add_argument('--subject', help='Subject do email')
    
    args = parser.parse_args()
    
    sharer = ResultsSharer(args.scan_dir)
    
    # Generates links/comandos
    sharer.generate_share_links()
    
    # Creates ZIP se solicitado
    if args.create_zip:
        sharer.create_shareable_package()
    
    # Sends email se solicitado
    if args.email:
        if not all([args.smtp_server, args.sender, args.sender_password, args.recipients]):
            print("\n❌ To send email, provide: --smtp-server, --sender, --sender-password, --recipients")
        else:
            sharer.send_email(
                smtp_server=args.smtp_server,
                smtp_port=args.smtp_port,
                sender_email=args.sender,
                sender_password=args.sender_password,
                recipient_emails=args.recipients,
                subject=args.subject
            )


if __name__ == "__main__":
    main()
