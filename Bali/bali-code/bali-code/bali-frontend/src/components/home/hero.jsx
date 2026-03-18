import React, { useState, useEffect } from "react";
import { Modal, Select, message } from "antd";
import Button from "../shared/button";
import { useNavigate } from "react-router-dom";
import { useVoiceToText } from "../../hooks/useVoiceToText";
import { useLanguage } from "../../context/LanguageContext";
import { API_BASE_URL } from "../../api/apiClient";

const { Option } = Select;

const Hero = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedVilla, setSelectedVilla] = useState(null);
  const [chatInput, setChatInput] = useState("");
  const [villas, setVillas] = useState([]);
  const navigate = useNavigate();

  const { language, toggleLanguage, t } = useLanguage();

  // Auto-trigger QR modal on first visit
  useEffect(() => {
    const hasSeenModal = localStorage.getItem('qr_modal_shown');
    if (!hasSeenModal) {
      setIsModalOpen(true);
      localStorage.setItem('qr_modal_shown', '1');
    }
  }, []);

  // Fetch real villas from API
  useEffect(() => {
    fetch(`${API_BASE_URL}/onboarding/villas`)
      .then((res) => res.json())
      .then((data) => {
        if (data.villas && data.villas.length > 0) {
          setVillas(data.villas);
        }
      })
      .catch(() => {
        // silently fallback — modal still usable without villa list
      });
  }, []);

  const { isListening, toggleListening } = useVoiceToText(
    (transcript) => setChatInput(transcript),
    (finalTranscript) => handleAutoSend(finalTranscript)
  );

  const handleAutoSend = (text) => {
    if (!text.trim()) return;
    // We need to make sure state is updated or pass text directly
    handleChat(text);
  };

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleOk = () => {
    setIsModalOpen(false);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };

  const handleVillaChange = (value) => {
    setSelectedVilla(value);
  };

  const handleChat = async (messageOverride) => {
    const textToSend = typeof messageOverride === 'string' ? messageOverride : chatInput;
    if (!textToSend.trim()) {
      message.warning("Please enter a message");
      return;
    }

    // Get or create user ID
    let userId = localStorage.getItem('userId');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('userId', userId);
    }

    // Navigate to chatbot with general chat type
    navigate("/chatbot", {
      state: {
        chatType: 'general', // This is the general chatbot
        userId: userId,
        activeTab: 'chat_tab', // Or whatever you want to call it
        initialMessage: {
          id: Date.now(),
          text: textToSend,
          sender: "user",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
          })
        }
      }
    });
    setChatInput("");
  };


  const handleKeyPress = (e) => {
    if (e.key === "Enter" && chatInput.trim()) {
      handleChat();
    }
  };

  const handleChatButtonClick = () => {
    handleChat();
  };

  return (
    <>
      <section className="hero relative max-w-[1392px] w-full flex flex-col justify-center items-center gap-[12px] rounded-[35px] sm:rounded-[50px] h-[500px] sm:h-[711px] z-[1] bg-no-repeat bg-cover bg-center">
        <img
          src="/assets/logo.svg"
          alt="logo"
          className="hero-logo absolute top-[30px] left-[30px]"
        />
        <button
          type="button"
          aria-label="Toggle language"
          className="language cursor-pointer flex justify-center items-center absolute top-[30px] right-[30px] rounded-full size-9 sm:size-[60px] border-[2px] border-solid border-white hover:bg-white hover:text-black transition-all bg-transparent"
          onClick={toggleLanguage}
        >
          <h5 className="text-[10px] sm:text-[22px] font-semibold text-white">
            {language}
          </h5>
        </button>

        {/* Hero headline overlay */}
        <div className="flex flex-col items-center text-center px-6 z-[2]">
          <h1 className="text-[28px] sm:text-[48px] lg:text-[56px] font-bold text-white leading-tight drop-shadow-lg">
            {t("hero_title") || "Welcome to EASY BALI"}
          </h1>
          <p className="text-[14px] sm:text-[18px] text-white/90 font-medium mt-2 drop-shadow">
            {t("hero_subtitle") || "Your personal travel companion"}
          </p>
        </div>

        <div className="hero-chat-input absolute -bottom-[7%] sm:-bottom-[10%] left-1/2 -translate-x-1/2 lg:left-0 lg:translate-x-0 z-[3] w-[90%] lg:w-full">
          <input
            type="text"
            placeholder={t("chat_placeholder")}
            className="w-full px-5 sm:px-10 pr-[100px] sm:pr-[150px] py-7 sm:py-10 rounded-[50px] text-[#8e8e8e] text-[16px] sm:text-[18px] border border-[#c6c6c6] placeholder:text-[#8e8e8e] outline-none focus:outline-none focus:border-[#c6c6c6] bg-white"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <div className="btns flex items-center justify-center gap-3 sm:gap-[30px] absolute bottom-6 sm:bottom-[17px] right-[35px]">
            <img
              src="/assets/mic.svg"
              alt="Voice Search"
              onClick={toggleListening}
              className={`cursor-pointer transition-all duration-300 ${isListening ? 'scale-150 mic-glow filter invert sepia(100%) saturate(10000%) hue-rotate(0deg) brightness(100%) contrast(100%)' : ''}`}
            />
            <img
              src="/assets/chat-btn.svg"
              alt=""
              className="cursor-pointer sm:size-full size-[33px]"
              onClick={handleChatButtonClick}
            />
          </div>
        </div>
      </section>

      <Modal
        closable={{ "aria-label": "Custom Close Button" }}
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
        className="scan-modal"
        width="90%"
        style={{ maxWidth: "1030px" }}
        centered
      >
        <div className="scan-modal-content">
          <div className="modal-inner-content">
            <h2 className="modal-title">{t("scan_qr_title")}</h2>
            <p className="modal-subtitle">
              {t("scan_qr_subtitle")}
            </p>
            <div className="qr-image-wrapper">
              <img src="/images/scanner.png" alt="img" className="qr-image" />
            </div>
            <p className="modal-description">
              You can also do this later if you would like to order any of our
              services.
            </p>
            <Button text={t("skip")} className="btn-primary modal-skip-btn" onClick={handleCancel} />
            <div className="villa-dropdown-wrapper">
              <Select
                placeholder={t("villas_placeholder")}
                className="villa-dropdown"
                onChange={handleVillaChange}
                value={selectedVilla}
                suffixIcon={
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <path
                      d="M6 9l6 6 6-6"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                }
              >
                {villas.map((villa) => (
                  <Option key={villa.villa_code || villa.villa_name} value={villa.villa_code || villa.villa_name}>
                    {villa.villa_name}
                  </Option>
                ))}
              </Select>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default Hero;