' WinWhisperPlus - Start ohne Konsolenfenster
' Dieses Skript startet die Anwendung, ohne ein Kommandozeilenfenster zu zeigen

Set objShell = CreateObject("WScript.Shell")
strPath = objShell.CurrentDirectory

' Starte main.py mit pythonw.exe (Python without console window)
objShell.Run "c:\python314\pythonw.exe """ & strPath & "\main.py""", 0, False
