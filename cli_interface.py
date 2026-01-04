"""
Enhanced CLI Interface for AI Primary Care Consultation System
Provides a user-friendly command-line interface with color coding and clear formatting
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional
import argparse

# Try to import colorama for colored output (optional)
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # Define dummy color constants if colorama not available
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

from medical_consultation_system import MedicalConsultationSystem
from config import Config, DevelopmentConfig, ProductionConfig, get_config


class ConsultationCLI:
    """Enhanced command-line interface for the medical consultation system"""
    
    def __init__(self, api_key: str, environment: str = "development", model: Optional[str] = None):
        """Initialize the CLI with configuration"""
        self.config = get_config(environment)
        selected_model = model or self.config.MODEL_NAME
        if model and model not in Config.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' is not supported. Choose from: {', '.join(Config.AVAILABLE_MODELS)}")

        self.system = MedicalConsultationSystem(api_key, selected_model)
        self.model_name = selected_model
        self.session_start = datetime.now()
        self.consultation_count = 0
        
    def print_header(self):
        """Print application header"""
        print("\n" + "=" * 70)
        print(f"{Style.BRIGHT}{Fore.CYAN}AI PRIMARY CARE CONSULTATION SYSTEM{Style.RESET_ALL}".center(70))
        print("=" * 70)
        print(f"{Fore.YELLOW}⚕️  Virtual Medical Assistant - Available 24/7 ⚕️{Fore.RESET}".center(70))
        print("=" * 70)
        
    def print_disclaimer(self):
        """Print medical disclaimer"""
        disclaimer = f"""
{Fore.RED}{Style.BRIGHT}IMPORTANT MEDICAL DISCLAIMER:{Style.RESET_ALL}
{Fore.YELLOW}• This system provides general health information only
• It cannot replace professional medical advice
• For emergencies, call 911 immediately
• Always consult a healthcare provider for medical concerns{Fore.RESET}
"""
        print(disclaimer)
        print("=" * 70)
        
    def print_instructions(self):
        """Print usage instructions"""
        instructions = f"""
{Fore.GREEN}How to use this system:{Fore.RESET}
1. Describe your symptoms clearly
2. Answer follow-up questions honestly
3. The system will provide guidance or recommend medical attention

{Fore.CYAN}Commands:{Fore.RESET}
• Type your symptoms to start a consultation
• Type 'quit' or 'exit' to leave
• Type 'help' for more information
• Type 'history' to view consultation history
"""
        print(instructions)
        
    def get_patient_input(self, prompt: str = "You: ") -> str:
        """Get input from patient with formatting"""
        print(f"{Fore.GREEN}{prompt}{Fore.RESET}", end="")
        return input()
    
    def print_assistant_message(self, message: str):
        """Print assistant message with formatting"""
        print(f"\n{Fore.CYAN}Assistant: {Fore.RESET}{message}\n")
    
    def print_emergency_message(self, message: str):
        """Print emergency message with special formatting"""
        print(f"\n{Back.RED}{Fore.WHITE}{Style.BRIGHT}⚠️  EMERGENCY RESPONSE ⚠️{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}{message}{Style.RESET_ALL}\n")
    
    def print_final_response(self, response: str, is_emergency: bool = False):
        """Print the final consultation response with appropriate formatting"""
        print("\n" + "=" * 70)
        if is_emergency:
            print(f"{Back.RED}{Fore.WHITE}{Style.BRIGHT}URGENT MEDICAL ATTENTION REQUIRED{Style.RESET_ALL}".center(70))
        else:
            print(f"{Fore.GREEN}{Style.BRIGHT}CONSULTATION SUMMARY{Style.RESET_ALL}".center(70))
        print("=" * 70)
        
        if is_emergency:
            self.print_emergency_message(response)
        else:
            print(f"{Fore.CYAN}{response}{Fore.RESET}")
        
        print("=" * 70)
    
    def save_consultation(self, complaint: str, response: str, patient_data: dict):
        """Save consultation to history file"""
        consultation = {
            "timestamp": datetime.now().isoformat(),
            "consultation_number": self.consultation_count,
            "initial_complaint": complaint,
            "final_response": response,
            "severity": patient_data.get("severity", "unknown"),
            "handoff_status": patient_data.get("handoff_status", "unknown")
        }
        
        history_file = "consultation_history.json"
        
        try:
            # Load existing history
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history = json.load(f)
            else:
                history = []
            
            # Append new consultation
            history.append(consultation)
            
            # Save updated history
            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)
                
            print(f"{Fore.GREEN}✓ Consultation saved to history{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}Note: Could not save consultation history: {e}{Fore.RESET}")
    
    def view_history(self):
        """View consultation history"""
        history_file = "consultation_history.json"
        
        if not os.path.exists(history_file):
            print(f"{Fore.YELLOW}No consultation history found.{Fore.RESET}")
            return
        
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}CONSULTATION HISTORY{Style.RESET_ALL}")
            print("=" * 70)
            
            for i, consultation in enumerate(history[-5:], 1):  # Show last 5
                timestamp = datetime.fromisoformat(consultation["timestamp"])
                print(f"\n{Fore.GREEN}#{i} - {timestamp.strftime('%Y-%m-%d %H:%M')}{Fore.RESET}")
                print(f"Complaint: {consultation['initial_complaint'][:50]}...")
                print(f"Severity: {consultation['severity']}/10")
                print(f"Status: {consultation['handoff_status']}")
            
            print("\n" + "=" * 70)
        except Exception as e:
            print(f"{Fore.RED}Error reading history: {e}{Fore.RESET}")
    
    def run_consultation(self, initial_complaint: str) -> tuple:
        """Run a single consultation"""
        self.consultation_count += 1
        print(f"\n{Fore.CYAN}Starting consultation #{self.consultation_count}...{Fore.RESET}")
        
        # Reset shared conversation history so agents see the full context
        self.system.conversation_history = []
        exchange_count = 1
        current_input = initial_complaint
        conversation_history = []
        
        while exchange_count <= 5:
            conversation_history.append(f"Patient: {current_input}")
            self.system.conversation_history.append(f"Patient: {current_input}")
            
            # Get response from history agent
            question, patient_data = self.system.history_agent(current_input, exchange_count)
            
            if patient_data:
                # Handoff triggered
                is_emergency = patient_data.get("handoff_status") == "EMERGENCY"
                
                if is_emergency:
                    print(f"\n{Fore.RED}⚠️  Emergency condition detected - processing immediately...{Fore.RESET}")
                else:
                    print(f"\n{Fore.YELLOW}Processing your information...{Fore.RESET}")
                
                # Get decision from decision agent
                decision = self.system.decision_agent(patient_data)
                
                # Polish with communication agent
                final_response = self.system.communication_agent(decision)
                
                return final_response, patient_data, is_emergency
            
            elif question:
                # Continue conversation
                conversation_history.append(f"Assistant: {question}")
                self.system.conversation_history.append(f"Assistant: {question}")
                self.print_assistant_message(question)
                
                current_input = self.get_patient_input()
                exchange_count += 1
                
                if current_input.lower() in ['quit', 'exit']:
                    return "Consultation cancelled by user.", {}, False
        
        # Forced handoff at exchange limit
        print(f"\n{Fore.YELLOW}Completing assessment...{Fore.RESET}")
        patient_data = {
            "handoff_status": "INCOMPLETE",
            "exchange_count": 5,
            "chief_complaint": initial_complaint[:100],
            "severity": 5,
            "patient_concern": "Assessment incomplete",
            "red_flags": {"present": [], "ruled_out": []}
        }
        
        decision = self.system.decision_agent(patient_data)
        final_response = self.system.communication_agent(decision)
        
        return final_response, patient_data, False
    
    def run(self):
        """Main CLI loop"""
        self.print_header()
        self.print_disclaimer()
        self.print_instructions()
        
        while True:
            try:
                # Get initial complaint
                user_input = self.get_patient_input("\nDescribe your symptoms (or type 'quit' to exit): ")
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit']:
                    self.print_goodbye()
                    break
                elif user_input.lower() == 'help':
                    self.print_instructions()
                    continue
                elif user_input.lower() == 'history':
                    self.view_history()
                    continue
                elif not user_input.strip():
                    print(f"{Fore.YELLOW}Please describe your symptoms or type 'quit' to exit.{Fore.RESET}")
                    continue
                
                # Run consultation
                final_response, patient_data, is_emergency = self.run_consultation(user_input)
                
                # Display final response
                self.print_final_response(final_response, is_emergency)
                
                # Save consultation
                self.save_consultation(user_input, final_response, patient_data)
                
                # Ask if user wants another consultation
                another = self.get_patient_input("\nWould you like to start another consultation? (yes/no): ")
                if another.lower() not in ['yes', 'y']:
                    self.print_goodbye()
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Consultation interrupted.{Fore.RESET}")
                self.print_goodbye()
                break
            except Exception as e:
                print(f"\n{Fore.RED}An error occurred: {e}{Fore.RESET}")
                print(f"{Fore.YELLOW}Please try again or contact support if the issue persists.{Fore.RESET}")
    
    def print_goodbye(self):
        """Print goodbye message with session summary"""
        session_duration = datetime.now() - self.session_start
        minutes = int(session_duration.total_seconds() / 60)
        
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}Thank you for using the AI Primary Care Consultation System{Fore.RESET}")
        print(f"Session duration: {minutes} minutes")
        print(f"Consultations completed: {self.consultation_count}")
        print(f"\n{Fore.YELLOW}Remember: For emergencies, always call 911{Fore.RESET}")
        print(f"{Fore.GREEN}Stay healthy! 👋{Fore.RESET}")
        print("=" * 70)


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="AI Primary Care Consultation System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)",
        default=os.getenv("OPENAI_API_KEY")
    )
    
    parser.add_argument(
        "--environment",
        type=str,
        choices=["development", "production", "test"],
        default="development",
        help="Environment configuration to use"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        choices=Config.AVAILABLE_MODELS,
        default=Config.MODEL_NAME,
        help="OpenAI model to use"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test suite instead of starting consultation"
    )
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        from test_medical_system import run_tests
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Check for API key
    if not args.api_key:
        print(f"{Fore.RED}Error: OpenAI API key is required.{Fore.RESET}")
        print("Set it via --api-key flag or OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # Start the CLI
    try:
        cli = ConsultationCLI(args.api_key, args.environment, args.model)
        cli.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}{Fore.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
