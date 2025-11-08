"""
File security utilities for malware detection and content scanning
"""
import os
import hashlib
import subprocess
import tempfile
from typing import Tuple, List, Dict, Optional
from datetime import datetime, timedelta
from flask import current_app


class FileSecurityScanner:
    """File security scanner for malware detection and content analysis"""
    
    def __init__(self):
        """Initialize security scanner"""
        self.quarantine_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'quarantine')
        self.scan_log_file = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'security_scan.log')
        self.ensure_quarantine_dir()
    
    def ensure_quarantine_dir(self):
        """Ensure quarantine directory exists"""
        os.makedirs(self.quarantine_dir, exist_ok=True)
    
    def scan_file(self, file_path: str) -> Tuple[bool, str, Dict]:
        """
        Comprehensive file security scan
        
        Returns:
            Tuple of (is_safe, message, scan_details)
        """
        scan_results = {
            'file_path': file_path,
            'scan_time': datetime.now(),
            'file_hash': self._calculate_file_hash(file_path),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'threats_found': [],
            'scan_methods': []
        }
        
        if not os.path.exists(file_path):
            return False, "File not found", scan_results
        
        # 1. Hash-based malware detection
        hash_result = self._check_malware_hash(scan_results['file_hash'])
        scan_results['scan_methods'].append('hash_check')
        if not hash_result[0]:
            scan_results['threats_found'].append(hash_result[1])
        
        # 2. File signature analysis
        signature_result = self._analyze_file_signature(file_path)
        scan_results['scan_methods'].append('signature_analysis')
        if not signature_result[0]:
            scan_results['threats_found'].append(signature_result[1])
        
        # 3. Content analysis
        content_result = self._analyze_file_content(file_path)
        scan_results['scan_methods'].append('content_analysis')
        if not content_result[0]:
            scan_results['threats_found'].append(content_result[1])
        
        # 4. ClamAV scan (if available)
        if self._is_clamav_available():
            clamav_result = self._clamav_scan(file_path)
            scan_results['scan_methods'].append('clamav_scan')
            if not clamav_result[0]:
                scan_results['threats_found'].append(clamav_result[1])
        
        # 5. Behavioral analysis
        behavior_result = self._behavioral_analysis(file_path)
        scan_results['scan_methods'].append('behavioral_analysis')
        if not behavior_result[0]:
            scan_results['threats_found'].append(behavior_result[1])
        
        # Log scan results
        self._log_scan_result(scan_results)
        
        # Determine overall result
        is_safe = len(scan_results['threats_found']) == 0
        message = "File is clean" if is_safe else f"Threats detected: {'; '.join(scan_results['threats_found'])}"
        
        # Quarantine if threats found
        if not is_safe:
            self._quarantine_file(file_path, scan_results)
        
        return is_safe, message, scan_results
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _check_malware_hash(self, file_hash: str) -> Tuple[bool, str]:
        """Check file hash against known malware database"""
        # This would integrate with threat intelligence feeds
        # For now, implement basic known bad hash checking
        
        known_malware_hashes = set()  # Load from database or file
        
        if file_hash in known_malware_hashes:
            return False, f"Known malware hash: {file_hash[:16]}..."
        
        return True, "Hash check passed"
    
    def _analyze_file_signature(self, file_path: str) -> Tuple[bool, str]:
        """Analyze file signature for suspicious patterns"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Read first 512 bytes
            
            # Check for suspicious signatures
            suspicious_signatures = [
                (b'\x4d\x5a', 'Windows PE executable'),
                (b'\x7f\x45\x4c\x46', 'Linux ELF executable'),
                (b'\xca\xfe\xba\xbe', 'Java class file'),
                (b'\xfe\xed\xfa\xce', 'Mach-O executable'),
                (b'\xfe\xed\xfa\xcf', 'Mach-O executable (64-bit)'),
            ]
            
            for signature, description in suspicious_signatures:
                if header.startswith(signature):
                    # Check if this is expected based on file extension
                    filename = os.path.basename(file_path)
                    if '.' in filename:
                        extension = filename.rsplit('.', 1)[1].lower()
                        # Allow executables only if they have appropriate extensions
                        if extension not in ['exe', 'dll', 'so', 'dylib', 'class']:
                            return False, f"Executable signature in non-executable file: {description}"
            
            return True, "File signature analysis passed"
            
        except Exception as e:
            return False, f"Signature analysis failed: {str(e)}"
    
    def _analyze_file_content(self, file_path: str) -> Tuple[bool, str]:
        """Analyze file content for malicious patterns"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Don't analyze very large files for performance
            if file_size > 50 * 1024 * 1024:  # 50MB
                return True, "File too large for content analysis"
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Convert to string for text analysis (ignore encoding errors)
            try:
                text_content = content.decode('utf-8', errors='ignore').lower()
            except:
                text_content = ""
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'eval(',
                'exec(',
                'system(',
                'shell_exec(',
                'passthru(',
                'base64_decode(',
                'gzinflate(',
                'str_rot13(',
                'javascript:',
                'vbscript:',
                'onload=',
                'onerror=',
                '<script',
                '</script>',
                'document.write',
                'document.cookie',
                'window.location',
            ]
            
            found_patterns = []
            for pattern in suspicious_patterns:
                if pattern in text_content:
                    found_patterns.append(pattern)
            
            if found_patterns:
                return False, f"Suspicious content patterns: {', '.join(found_patterns[:5])}"
            
            # Check for embedded executables in documents
            if content.find(b'MZ') != -1 and content.find(b'This program cannot be run in DOS mode') != -1:
                return False, "Embedded executable detected in document"
            
            return True, "Content analysis passed"
            
        except Exception as e:
            return False, f"Content analysis failed: {str(e)}"
    
    def _is_clamav_available(self) -> bool:
        """Check if ClamAV is available"""
        try:
            result = subprocess.run(['clamscan', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _clamav_scan(self, file_path: str) -> Tuple[bool, str]:
        """Scan file with ClamAV"""
        try:
            result = subprocess.run([
                'clamscan', '--no-summary', '--infected', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, "ClamAV scan clean"
            elif result.returncode == 1:
                # Virus found
                output_lines = result.stdout.strip().split('\n')
                virus_info = output_lines[-1] if output_lines else "Unknown virus"
                return False, f"ClamAV detected: {virus_info}"
            else:
                return False, f"ClamAV scan error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "ClamAV scan timeout"
        except Exception as e:
            return False, f"ClamAV scan failed: {str(e)}"
    
    def _behavioral_analysis(self, file_path: str) -> Tuple[bool, str]:
        """Perform behavioral analysis of file"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Check for suspicious file characteristics
            suspicious_indicators = []
            
            # Very small files with executable extensions
            if file_size < 100 and filename.lower().endswith(('.exe', '.scr', '.bat', '.cmd')):
                suspicious_indicators.append("Very small executable file")
            
            # Files with double extensions
            if filename.count('.') > 1:
                parts = filename.split('.')
                if len(parts) >= 3 and parts[-2].lower() in ['exe', 'scr', 'bat', 'cmd']:
                    suspicious_indicators.append("Double extension detected")
            
            # Files with suspicious names
            suspicious_names = [
                'autorun.inf', 'desktop.ini', 'thumbs.db', '.htaccess',
                'web.config', 'config.php', 'wp-config.php'
            ]
            
            if filename.lower() in suspicious_names:
                suspicious_indicators.append(f"Suspicious filename: {filename}")
            
            # Check modification time (files modified in the future)
            try:
                mtime = os.path.getmtime(file_path)
                if mtime > datetime.now().timestamp() + 3600:  # 1 hour in future
                    suspicious_indicators.append("File modification time in future")
            except:
                pass
            
            if suspicious_indicators:
                return False, f"Behavioral analysis flags: {'; '.join(suspicious_indicators)}"
            
            return True, "Behavioral analysis passed"
            
        except Exception as e:
            return False, f"Behavioral analysis failed: {str(e)}"
    
    def _quarantine_file(self, file_path: str, scan_results: Dict):
        """Move suspicious file to quarantine"""
        try:
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quarantine_filename = f"{timestamp}_{filename}"
            quarantine_path = os.path.join(self.quarantine_dir, quarantine_filename)
            
            # Move file to quarantine
            os.rename(file_path, quarantine_path)
            
            # Create quarantine info file
            info_file = quarantine_path + '.info'
            with open(info_file, 'w') as f:
                f.write(f"Original path: {file_path}\n")
                f.write(f"Quarantine time: {scan_results['scan_time']}\n")
                f.write(f"File hash: {scan_results['file_hash']}\n")
                f.write(f"Threats: {'; '.join(scan_results['threats_found'])}\n")
                f.write(f"Scan methods: {', '.join(scan_results['scan_methods'])}\n")
            
            current_app.logger.warning(f"File quarantined: {file_path} -> {quarantine_path}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to quarantine file {file_path}: {str(e)}")
    
    def _log_scan_result(self, scan_results: Dict):
        """Log scan results to file"""
        try:
            with open(self.scan_log_file, 'a') as f:
                log_entry = {
                    'timestamp': scan_results['scan_time'].isoformat(),
                    'file_path': scan_results['file_path'],
                    'file_hash': scan_results['file_hash'],
                    'file_size': scan_results['file_size'],
                    'threats_count': len(scan_results['threats_found']),
                    'threats': scan_results['threats_found'],
                    'scan_methods': scan_results['scan_methods']
                }
                f.write(f"{log_entry}\n")
        except Exception as e:
            current_app.logger.error(f"Failed to log scan result: {str(e)}")
    
    def get_quarantine_files(self) -> List[Dict]:
        """Get list of quarantined files"""
        quarantine_files = []
        
        try:
            if not os.path.exists(self.quarantine_dir):
                return quarantine_files
            
            for filename in os.listdir(self.quarantine_dir):
                if filename.endswith('.info'):
                    continue
                
                file_path = os.path.join(self.quarantine_dir, filename)
                info_path = file_path + '.info'
                
                file_info = {
                    'filename': filename,
                    'quarantine_path': file_path,
                    'size': os.path.getsize(file_path),
                    'quarantine_time': datetime.fromtimestamp(os.path.getctime(file_path)),
                    'original_path': 'Unknown',
                    'threats': 'Unknown'
                }
                
                # Read info file if exists
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            info_content = f.read()
                            for line in info_content.split('\n'):
                                if line.startswith('Original path:'):
                                    file_info['original_path'] = line.split(':', 1)[1].strip()
                                elif line.startswith('Threats:'):
                                    file_info['threats'] = line.split(':', 1)[1].strip()
                    except:
                        pass
                
                quarantine_files.append(file_info)
            
            # Sort by quarantine time (newest first)
            quarantine_files.sort(key=lambda x: x['quarantine_time'], reverse=True)
            
        except Exception as e:
            current_app.logger.error(f"Failed to get quarantine files: {str(e)}")
        
        return quarantine_files
    
    def cleanup_old_quarantine_files(self, days_old: int = 30):
        """Clean up quarantine files older than specified days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            
            for filename in os.listdir(self.quarantine_dir):
                file_path = os.path.join(self.quarantine_dir, filename)
                
                if os.path.getctime(file_path) < cutoff_time.timestamp():
                    os.remove(file_path)
                    
                    # Remove info file if exists
                    info_path = file_path + '.info'
                    if os.path.exists(info_path):
                        os.remove(info_path)
                    
                    current_app.logger.info(f"Cleaned up old quarantine file: {filename}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to cleanup quarantine files: {str(e)}")


# Utility functions

def scan_uploaded_file(file_path: str) -> Tuple[bool, str, Dict]:
    """Scan an uploaded file for security threats"""
    scanner = FileSecurityScanner()
    return scanner.scan_file(file_path)

def get_quarantined_files() -> List[Dict]:
    """Get list of quarantined files"""
    scanner = FileSecurityScanner()
    return scanner.get_quarantine_files()

def cleanup_quarantine(days_old: int = 30):
    """Clean up old quarantine files"""
    scanner = FileSecurityScanner()
    scanner.cleanup_old_quarantine_files(days_old)