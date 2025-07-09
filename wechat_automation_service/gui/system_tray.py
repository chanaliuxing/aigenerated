#!/usr/bin/env python3
"""
System Tray Application for WeChat Automation Service
Provides GUI interface for service management
"""

import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                                QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QTextEdit, QListWidget,
                                QTabWidget, QGroupBox, QCheckBox, QLineEdit,
                                QMessageBox, QDialog, QFormLayout, QSpinBox)
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt5.QtGui import QIcon, QPixmap, QFont
    PYQT_AVAILABLE = True
except ImportError:
    logger.warning("PyQt5 not available, system tray will be disabled")
    PYQT_AVAILABLE = False
    
    # Create dummy classes for when PyQt5 is not available
    class QApplication:
        def __init__(self, *args): pass
        def exec_(self): pass
    
    class QSystemTrayIcon:
        def __init__(self, *args): pass
        def show(self): pass
        def hide(self): pass
        def setToolTip(self, *args): pass
        def setContextMenu(self, *args): pass
        def showMessage(self, *args): pass
    
    class QMainWindow:
        def __init__(self, *args): pass
        def show(self): pass
        def hide(self): pass
        def close(self): pass
    
    class QWidget:
        def __init__(self, *args): pass
    
    class QMenu:
        def __init__(self, *args): pass
        def addAction(self, *args): pass
        def addSeparator(self): pass
    
    class QAction:
        def __init__(self, *args): pass
        def triggered(self): 
            class DummySignal:
                def connect(self, *args): pass
            return DummySignal()
    
    class QDialog:
        def __init__(self, *args): pass
        def exec_(self): pass
        def accept(self): pass
        def reject(self): pass
    
    class QFormLayout:
        def __init__(self, *args): pass
        def addRow(self, *args): pass
    
    class QLineEdit:
        def __init__(self, *args): pass
    
    class QCheckBox:
        def __init__(self, *args): pass
    
    class QPushButton:
        def __init__(self, *args): pass
        def clicked(self):
            class DummySignal:
                def connect(self, *args): pass
            return DummySignal()
    
    class QHBoxLayout:
        def __init__(self, *args): pass
        def addWidget(self, *args): pass

class SystemTrayApp(QSystemTrayIcon):
    """System tray application for WeChat automation service"""
    
    def __init__(self, service_instance):
        if not PYQT_AVAILABLE:
            logger.warning("PyQt5 not available, system tray disabled")
            return
            
        super().__init__()
        
        self.service = service_instance
        self.main_window = None
        
        # Create tray icon
        self.create_tray_icon()
        
        # Create context menu
        self.create_context_menu()
        
        # Set up timer for status updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # Update every 5 seconds
        
        # Show tray icon
        self.show()
        
        logger.info("System tray application initialized")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # Create a simple icon (in real implementation, use proper icon file)
            icon = QIcon()
            
            # Set tooltip
            self.setToolTip("WeChat Automation Service")
            
            # Connect double-click to show main window
            self.activated.connect(self.on_tray_icon_activated)
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
    
    def create_context_menu(self):
        """Create context menu for tray icon"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            menu = QMenu()
            
            # Show main window action
            show_action = QAction("Show Dashboard", self)
            show_action.triggered.connect(self.show_main_window)
            menu.addAction(show_action)
            
            menu.addSeparator()
            
            # Service status action
            status_action = QAction("Service Status", self)
            status_action.triggered.connect(self.show_status)
            menu.addAction(status_action)
            
            # Start/Stop service actions
            start_action = QAction("Start Service", self)
            start_action.triggered.connect(self.start_service)
            menu.addAction(start_action)
            
            stop_action = QAction("Stop Service", self)
            stop_action.triggered.connect(self.stop_service)
            menu.addAction(stop_action)
            
            menu.addSeparator()
            
            # Settings action
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.show_settings)
            menu.addAction(settings_action)
            
            menu.addSeparator()
            
            # Exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.exit_application)
            menu.addAction(exit_action)
            
            self.setContextMenu(menu)
            
        except Exception as e:
            logger.error(f"Error creating context menu: {e}")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if not PYQT_AVAILABLE:
            return
            
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
    
    def show_main_window(self):
        """Show main dashboard window"""
        if not PYQT_AVAILABLE:
            return
            
        if self.main_window is None:
            self.main_window = MainWindow(self.service)
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    def show_status(self):
        """Show service status"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            status = "Running" if self.service.running else "Stopped"
            active_workflows = len(self.service.active_workflows) if hasattr(self.service, 'active_workflows') else 0
            
            message = f"Service Status: {status}\nActive Workflows: {active_workflows}"
            
            self.showMessage(
                "WeChat Automation Service",
                message,
                QSystemTrayIcon.Information,
                3000
            )
            
        except Exception as e:
            logger.error(f"Error showing status: {e}")
    
    def start_service(self):
        """Start the service"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if not self.service.running:
                # In a real implementation, this would start the service
                logger.info("Service start requested from tray")
                self.showMessage(
                    "WeChat Automation Service",
                    "Service starting...",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                self.showMessage(
                    "WeChat Automation Service",
                    "Service is already running",
                    QSystemTrayIcon.Information,
                    2000
                )
                
        except Exception as e:
            logger.error(f"Error starting service: {e}")
    
    def stop_service(self):
        """Stop the service"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if self.service.running:
                # In a real implementation, this would stop the service
                logger.info("Service stop requested from tray")
                self.showMessage(
                    "WeChat Automation Service",
                    "Service stopping...",
                    QSystemTrayIcon.Information,
                    2000
                )
            else:
                self.showMessage(
                    "WeChat Automation Service",
                    "Service is not running",
                    QSystemTrayIcon.Information,
                    2000
                )
                
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
    
    def show_settings(self):
        """Show settings dialog"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            dialog = SettingsDialog(self.service)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
    
    def exit_application(self):
        """Exit the application"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # Stop the service
            if self.service.running:
                self.service.running = False
            
            # Close main window if open
            if self.main_window:
                self.main_window.close()
            
            # Hide tray icon
            self.hide()
            
            # Exit application
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"Error exiting application: {e}")
    
    def update_status(self):
        """Update tray icon status"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if self.service.running:
                self.setToolTip("WeChat Automation Service - Running")
            else:
                self.setToolTip("WeChat Automation Service - Stopped")
                
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def close(self):
        """Close the system tray"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.hide()
            if self.main_window:
                self.main_window.close()
                
        except Exception as e:
            logger.error(f"Error closing system tray: {e}")

class MainWindow(QMainWindow):
    """Main dashboard window"""
    
    def __init__(self, service_instance):
        if not PYQT_AVAILABLE:
            return
            
        super().__init__()
        
        self.service = service_instance
        
        self.setWindowTitle("WeChat Automation Service Dashboard")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tab content
        self.create_status_tab()
        self.create_workflows_tab()
        self.create_messages_tab()
        self.create_logs_tab()
        
        logger.info("Main window initialized")
    
    def create_status_tab(self):
        """Create status tab"""
        if not PYQT_AVAILABLE:
            return
            
        status_widget = QWidget()
        layout = QVBoxLayout(status_widget)
        
        # Service status group
        status_group = QGroupBox("Service Status")
        status_layout = QFormLayout(status_group)
        
        self.status_label = QLabel("Running" if self.service.running else "Stopped")
        status_layout.addRow("Status:", self.status_label)
        
        self.workflows_label = QLabel("0")
        status_layout.addRow("Active Workflows:", self.workflows_label)
        
        layout.addWidget(status_group)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Service")
        self.start_button.clicked.connect(self.start_service)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Service")
        self.stop_button.clicked.connect(self.stop_service)
        buttons_layout.addWidget(self.stop_button)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        self.tabs.addTab(status_widget, "Status")
    
    def create_workflows_tab(self):
        """Create workflows tab"""
        if not PYQT_AVAILABLE:
            return
            
        workflows_widget = QWidget()
        layout = QVBoxLayout(workflows_widget)
        
        # Active workflows list
        self.workflows_list = QListWidget()
        layout.addWidget(QLabel("Active Workflows:"))
        layout.addWidget(self.workflows_list)
        
        self.tabs.addTab(workflows_widget, "Workflows")
    
    def create_messages_tab(self):
        """Create messages tab"""
        if not PYQT_AVAILABLE:
            return
            
        messages_widget = QWidget()
        layout = QVBoxLayout(messages_widget)
        
        # Message history
        self.messages_list = QListWidget()
        layout.addWidget(QLabel("Message History:"))
        layout.addWidget(self.messages_list)
        
        self.tabs.addTab(messages_widget, "Messages")
    
    def create_logs_tab(self):
        """Create logs tab"""
        if not PYQT_AVAILABLE:
            return
            
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Log output
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Service Logs:"))
        layout.addWidget(self.log_text)
        
        self.tabs.addTab(logs_widget, "Logs")
    
    def start_service(self):
        """Start service"""
        if not PYQT_AVAILABLE:
            return
            
        logger.info("Start service requested from dashboard")
        self.status_label.setText("Starting...")
    
    def stop_service(self):
        """Stop service"""
        if not PYQT_AVAILABLE:
            return
            
        logger.info("Stop service requested from dashboard")
        self.status_label.setText("Stopping...")

class SettingsDialog(QDialog):
    """Settings dialog"""
    
    def __init__(self, service_instance):
        if not PYQT_AVAILABLE:
            return
            
        super().__init__()
        
        self.service = service_instance
        
        self.setWindowTitle("Settings")
        self.setGeometry(150, 150, 400, 300)
        
        layout = QFormLayout(self)
        
        # Settings fields
        self.orchestrator_url = QLineEdit("ws://localhost:3000")
        layout.addRow("Orchestrator URL:", self.orchestrator_url)
        
        self.machine_id = QLineEdit("machine_001")
        layout.addRow("Machine ID:", self.machine_id)
        
        self.auto_start = QCheckBox()
        layout.addRow("Auto Start:", self.auto_start)
        
        self.log_level = QLineEdit("INFO")
        layout.addRow("Log Level:", self.log_level)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addRow(buttons_layout)
    
    def save_settings(self):
        """Save settings"""
        if not PYQT_AVAILABLE:
            return
            
        logger.info("Settings saved")
        self.accept()

# Dummy implementations for when PyQt5 is not available
class DummySystemTrayApp:
    """Dummy system tray app when PyQt5 is not available"""
    
    def __init__(self, service_instance):
        self.service = service_instance
        logger.warning("System tray disabled - PyQt5 not available")
    
    def show(self):
        pass
    
    def close(self):
        pass

# Export the appropriate class based on PyQt5 availability
if PYQT_AVAILABLE:
    SystemTrayApp = SystemTrayApp
else:
    SystemTrayApp = DummySystemTrayApp
