// static/script.js मध्ये हा कोड जोडा

function showHint() {
    // 1. Hint चा खर्च आणि युजरचे Coins मिळवा (Navbar मधून)
    // सध्या आपण Navbar मधील XP/Coins Counter वरून डमी डेटा वाचूया
    const coinsElement = document.getElementById('virtual-currency-counter');
    const currentCoins = parseInt(coinsElement ? coinsElement.textContent : '0') || 0;
    
    // 2. HTML मधून Hint चा तपशील आणि खर्च मिळवा
    // (ही व्हॅल्यू challenge_editor.html मधून data-cost या attribute मधून यायला हवी)
    // सध्या आपण 5 Coins चा खर्च आणि एक डमी Hint वापरूया.
    const hintCost = 5; 
    const hintMessage = "Hint: Remember to use the '+' operator inside the printf function to perform the addition.";
    
    const hintArea = document.getElementById('hintArea');
    const hintTextElement = document.getElementById('hintText');
    
    if (hintArea.classList.contains('hidden')) {
        // Coins तपासा
        if (currentCoins < hintCost) {
            alert("Not enough Coins! You need " + hintCost + " Coins to unlock this hint.");
            return;
        }

        // Coins कमी करण्याची क्रिया (अद्याप Back-End ला जोडलेली नाही)
        // तात्पुरता UI update:
        // coinsElement.textContent = currentCoins - hintCost; 
        
        // Hint दाखवा
        if (hintTextElement) {
            hintTextElement.textContent = hintMessage;
        }
        hintArea.classList.remove('hidden');
        alert(`Hint Unlocked! ${hintCost} Coins deducted (Backend logic needed).`);
    }
}

// 🔴 महत्वाचे 🔴:
// तुमचे challenge_editor.html मध्ये Hint बटन showHint() ला कॉल करत असल्याने, 
// हा code तुमच्या Global scope मध्ये (कोणत्याही function च्या आत नाही) असायला हवा.

// Note: जर तुम्ही एका वेगळ्या JS फाईलमध्ये काम करत असाल, तर या फंक्शनला त्या फाईलमध्ये ठेवा.