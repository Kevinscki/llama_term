sudo apt install snap -y
sudo apt install snapd -y
sudo systemctl enable --now snapd
sudo snap install ollama #or get it officially
ollama pull qwen2.5-coder:3b
