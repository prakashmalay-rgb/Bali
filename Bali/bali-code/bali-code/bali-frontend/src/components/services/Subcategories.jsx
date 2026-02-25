import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useVoiceToText } from "../../hooks/useVoiceToText";
import { chatAPI } from '../../api/chatApi';
import { useLanguage } from '../../context/LanguageContext';
import Slider from "react-slick"
import "slick-carousel/slick/slick.css"
import "slick-carousel/slick/slick-theme.css"
import balilogo from '../../assets/images/balilogo.svg'
import secondlogo from '../../assets/images/secondlogo.svg'
import bottomRightPng from '../../assets/images/right-bottom.png'
import topLeftPng from '../../assets/images/top-left.png'
import { getSubCategory, getServiceItems } from './api.jsx'

const SubCategories = () => {
  const { t, language, toggleLanguage } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [screenSize, setScreenSize] = useState('desktop');
  const [sliderData, setSliderData] = useState([]);
  const [loading, setLoading] = useState(true);

  // ← NEW: Track which button is loading
  const [buttonLoading, setButtonLoading] = useState(null);
  const [chatInput, setChatInput] = useState("");

  const { isListening, toggleListening } = useVoiceToText(
    (transcript) => setChatInput(transcript),
    (finalTranscript) => handleAutoSend(finalTranscript)
  );

  const handleAutoSend = (text) => {
    if (!text.trim()) return;
    handleGeneralChat(text);
  };

  const handleGeneralChat = async (messageOverride) => {
    const textToSend = typeof messageOverride === 'string' ? messageOverride : chatInput;
    if (!textToSend.trim()) return;

    const currentUserId = localStorage.getItem("userId") || chatAPI.getUserId();
    navigate('/chatbot', {
      state: {
        chatType: 'general',
        userId: currentUserId,
        initialMessage: {
          id: Date.now(),
          text: textToSend,
          sender: "user",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        },
        activeTab: "Chat"
      }
    });
    setChatInput("");
  };

  const defaultSliderData = [
    {
      id: 1,
      title: t("coming_soon"),
      subtitle: t("coming_soon"),
      description: t("coming_soon_desc"),
      buttonText: t("back"),
      image: "https://easybali.s3.ap-southeast-2.amazonaws.com/EASYBali+-+Web+Images/imagebrand-webp/sub-massage.webp"
    }
  ];

  // Initial data fetch (UNCHANGED)
  useEffect(() => {
    const fetchData = async () => {
      const mainMenu = location.state?.mainMenu;
      const passedData = location.state?.data;

      if (passedData && passedData.length > 0) {
        const transformedData = passedData.map((item, index) => ({
          id: index + 1,
          title: item.subcategory,
          subtitle: item.subcategory,
          description: item.description,
          buttonText: item.button || "See Details",
          image: item.picture
        }));
        setSliderData(transformedData);
      } else if (mainMenu) {
        try {
          setLoading(true);
          const response = await getSubCategory(mainMenu);
          const transformedData = response.data.map((item, index) => ({
            id: index + 1,
            title: item.subcategory,
            subtitle: item.subcategory,
            description: item.description,
            buttonText: item.button || "See Details",
            image: item.picture
          }));
          setSliderData(transformedData);
        } catch (err) {
          console.error('Error fetching subcategories:', err);
          setSliderData(defaultSliderData);
        }
      } else {
        setSliderData(defaultSliderData);
      }
      setLoading(false);
    };

    fetchData();
  }, [location.state]);

  // Screen size detection (UNCHANGED)
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width <= 768) setScreenSize('mobile');
      else if (width <= 1024) setScreenSize('tablet');
      else setScreenSize('desktop');
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // ← UPDATED: Button-specific loading!
  const handleSeeOptionsClick = async (subtitle, slideId) => {
    setButtonLoading(slideId); // Show loading ONLY for this button

    try {
      const response = await getServiceItems(subtitle);
      navigate('/serviceitems', {
        state: {
          mainMenu: subtitle,
          data: response.data
        }
      });
    } catch (error) {
      console.error('Error fetching details:', error);
      navigate('/serviceitems', {
        state: {
          mainMenu: subtitle,
          data: []
        }
      });
    } finally {
      setButtonLoading(null); // Reset loading
    }
  };

  // Custom arrows (UNCHANGED)
  const CustomPrevArrow = ({ onClick }) => (
    <button className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 bg-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:shadow-xl transition-all" onClick={onClick}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path d="M15 18l-6-6 6-6" stroke="#333" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  );

  const CustomNextArrow = ({ onClick }) => (
    <button className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 bg-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:shadow-xl transition-all" onClick={onClick}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path d="M9 18l6-6-6-6" stroke="#333" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  );

  const getSliderSettings = () => {
    const baseSettings = { infinite: true, speed: 500, dots: true, swipe: true, swipeToSlide: true, draggable: true, touchThreshold: 10 };
    if (screenSize === 'mobile') return { ...baseSettings, slidesToShow: 1, centerMode: false, centerPadding: "0px", focusOnSelect: false, arrows: false };
    else if (screenSize === 'tablet') return { ...baseSettings, slidesToShow: 2, centerMode: true, centerPadding: "0", focusOnSelect: true, prevArrow: <CustomPrevArrow />, nextArrow: <CustomNextArrow /> };
    else return { ...baseSettings, className: "center", slidesToShow: 3, centerMode: true, centerPadding: "0", focusOnSelect: true, prevArrow: <CustomPrevArrow />, nextArrow: <CustomNextArrow /> };
  };

  const settings = getSliderSettings();

  if (loading) {
    return (
      <div className='bg-white min-h-screen flex items-center justify-center'>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#FF8000]"></div>
      </div>
    );
  }

  return (
    <div className='bg-white min-h-screen flex flex-col justify-between background-class relative'>
      <img src={topLeftPng} alt="Top Left Icon" className="absolute top-[0px] left-[0px] sm:left-[0px] md:left-[0px] w-[350px] sm:w-[200px] md:w-[400px] opacity-60 z-0" />
      <img src={bottomRightPng} alt="Bottom Right Icon" className="absolute bottom-0 right-0 w-[300px] sm:w-[250px] md:w-[450px] opacity-60 z-0" />

      <div className='relative z-10'>
        <div className='flex items-center justify-between px-[24px] lg:px-[100px] py-[24px] lg:py-[40px]'>
          <img src={balilogo} alt='Bali' onClick={() => navigate('/')} className='cursor-pointer h-[30px] lg:h-auto' />
          <div className='flex items-center gap-4'>
            <img src={secondlogo} alt='Second Logo' className='w-[62px] h-[32px] lg:h-[40px] cursor-pointer' />
            <div
              className="flex justify-center items-center size-8 sm:size-12 rounded-full border-[1px] border-solid border-black cursor-pointer hover:bg-black hover:text-white transition-all ml-2"
              onClick={toggleLanguage}
            >
              <h6 className="font-semibold text-xs sm:text-sm">{language}</h6>
            </div>
          </div>
        </div>
      </div>

      <div className='relative mb-[30px] sm:mb-[60px] mobile-slider-container z-10'>
        <Slider {...settings}>
          {sliderData.map((slide) => (
            <div key={slide.id} className='px-[20px] md:px-[20px] slider-item'>
              <div
                className='rounded-[30px] sm:rounded-[50px] flex flex-col items-center justify-center w-full mx-auto slider-card transition-all duration-300 relative overflow-hidden h-[400px] sm:h-[450px] md:h-[500px]'
                style={{
                  backgroundImage: `url(${slide.image})`,
                  backgroundSize: 'cover',
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'center'
                }}
              >
                <div
                  className='absolute bottom-0 left-0 right-0 rounded-b-[30px] sm:rounded-b-[50px]'
                  style={{
                    height: '60%',
                    background: 'linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 50%, transparent 100%)',
                    pointerEvents: 'none'
                  }}
                ></div>

                <div className='relative z-10 flex flex-col items-center justify-end w-full h-full px-[15px] pb-[20px] sm:pb-[25px]'>
                  <div className='w-full text-center space-y-[8px] sm:space-y-[10px]'>
                    <p className='text-white font-semibold text-[18px] sm:text-[22px] md:text-[24px]'>{slide.subtitle}</p>
                    <p className='text-[13px] sm:text-[15px] md:text-[16px] font-medium text-white text-center px-[10px] sm:px-[20px] md:px-[30px]'>
                      {slide.description}
                    </p>
                  </div>

                  <div className='px-[15px] sm:px-[20px] md:px-[24px] w-full mt-[12px] sm:mt-[15px] md:mt-[18px]'>
                    {/* ← MAGIC: BUTTON-SPECIFIC LOADING! */}
                    <button
                      className={`h-[45px] sm:h-[55px] md:h-[60px] rounded-[50px] text-white font-medium text-[14px] sm:text-[16px] md:text-[18px] w-full transition-all ${buttonLoading === slide.id
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-[#FF8000] hover:bg-[#e6720a] cursor-pointer'
                        } flex items-center justify-center gap-2`}
                      onClick={() => handleSeeOptionsClick(slide.subtitle, slide.id)}
                      disabled={buttonLoading === slide.id}
                    >
                      {buttonLoading === slide.id ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          {t("loading")}
                        </>
                      ) : (
                        slide.buttonText === "See Options" ? t("see_options") : slide.buttonText === "See Details" ? t("see_details") : slide.buttonText
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Slider>
      </div>

      <div className='px-[24px] lg:px-[100px] z-10'>
        <div className='rounded-full bg-white shadow-lg flex px-[40px] py-[20px] items-center justify-between h-[85px] mb-[30px] border-class'>
          <input
            type="text"
            placeholder={t("chat_placeholder")}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleGeneralChat()}
            className="w-[90%] py-4 sm:py-6 rounded-[50px] text-[#333] text-[16px] sm:text-[18px] placeholder:text-[#8e8e8e] outline-none"
          />
          <div className='flex items-center gap-4'>
            <img
              src="/assets/mic.svg"
              alt="Voice Search"
              onClick={toggleListening}
              className={`cursor-pointer transition-all duration-300 ${isListening ? 'scale-150 mic-glow filter invert sepia(100%) saturate(10000%) hue-rotate(0deg) brightness(100%) contrast(100%)' : ''}`}
            />
            <img
              src="/assets/chat-btn.svg"
              alt=""
              onClick={handleGeneralChat}
              className="cursor-pointer w-[35px] h-[35px] sm:w-[50px] sm:h-[50px]"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SubCategories