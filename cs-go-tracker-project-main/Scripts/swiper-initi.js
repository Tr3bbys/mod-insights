export function initSwiper() {
    return new Swiper('.swiper', {
        // Show 1 slide on narrow screens, 2 once there's room
        slidesPerView: 1,
        breakpoints: {
            700: { slidesPerView: 2 },
        },

        // Add space between slides (in pixels)
        spaceBetween: 20,

        // Let slide height follow its content instead of a fixed px height
        autoHeight: true,

        // Maintain responsiveness across screen sizes
        loop: true,

        // Navigation arrows
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });
}