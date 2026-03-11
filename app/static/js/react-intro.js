/**
 * Al-Huda — React-Powered Intro Animation
 * A premium, animated launch screen with particle effects and smooth transitions.
 */
const { useState, useEffect, useRef, createElement: h } = React;

// ─────────────────────────────────────────────────────────
// Floating Particle Component
// ─────────────────────────────────────────────────────────
function Particle({ delay, size, x, duration, color }) {
    const style = {
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: '50%',
        background: color || 'rgba(16, 185, 129, 0.6)',
        left: x + '%',
        bottom: '-10px',
        animation: `particleRise ${duration}s ease-out ${delay}s infinite`,
        opacity: 0,
        filter: 'blur(0.5px)',
        boxShadow: `0 0 ${size * 2}px ${color || 'rgba(16, 185, 129, 0.3)'}`,
    };
    return h('div', { style });
}

// ─────────────────────────────────────────────────────────
// Orbit Ring — a rotating container with dots placed around it
// ─────────────────────────────────────────────────────────
function OrbitRing({ count, radius, duration, reverse, dotSize }) {
    const containerStyle = {
        position: 'absolute',
        width: radius * 2,
        height: radius * 2,
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        animation: `orbit ${duration}s linear infinite ${reverse ? 'reverse' : ''}`,
    };

    const dots = Array.from({ length: count }, (_, i) => {
        const angle = (360 / count) * i;
        const rad = (angle * Math.PI) / 180;
        const x = radius + Math.cos(rad) * radius - (dotSize || 5) / 2;
        const y = radius + Math.sin(rad) * radius - (dotSize || 5) / 2;
        return h('div', {
            key: i,
            style: {
                position: 'absolute',
                width: dotSize || 5,
                height: dotSize || 5,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #059669, #34d399)',
                boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)',
                left: x,
                top: y,
                opacity: 0.7 + (i % 3) * 0.1,
            },
        });
    });

    return h('div', { style: containerStyle }, ...dots);
}

// ─────────────────────────────────────────────────────────
// Ripple Ring Component
// ─────────────────────────────────────────────────────────
function RippleRing({ delay, maxSize }) {
    const style = {
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: 0,
        height: 0,
        borderRadius: '50%',
        border: '2px solid rgba(16, 185, 129, 0.3)',
        transform: 'translate(-50%, -50%)',
        animation: `rippleExpand 3s ease-out ${delay}s infinite`,
        opacity: 0,
    };
    return h('div', { style, 'data-max': maxSize });
}

// ─────────────────────────────────────────────────────────
// Main Intro Animation Component
// ─────────────────────────────────────────────────────────
function IntroAnimation({ onComplete }) {
    const [phase, setPhase] = useState('entering');  // entering → showing → exiting → done
    const [fontsReady, setFontsReady] = useState(false);
    const containerRef = useRef(null);

    // Font loading
    useEffect(() => {
        const checkFonts = async () => {
            try {
                await document.fonts.ready;
                const loaded = document.fonts.check('1em "Material Symbols Outlined"');
                setFontsReady(true);
                document.body.classList.add('fonts-loaded');
                if (!loaded) {
                    setTimeout(() => document.body.classList.add('fonts-loaded'), 100);
                }
            } catch {
                setFontsReady(true);
                document.body.classList.add('fonts-loaded');
            }
        };
        checkFonts();
        setTimeout(() => setFontsReady(true), 500);
    }, []);

    // Phase transitions
    useEffect(() => {
        document.body.style.opacity = '1';

        const showTimer = setTimeout(() => setPhase('showing'), 300);
        const exitTimer = setTimeout(() => setPhase('exiting'), 3800);
        const doneTimer = setTimeout(() => {
            setPhase('done');
            if (onComplete) onComplete();
        }, 4500);

        return () => {
            clearTimeout(showTimer);
            clearTimeout(exitTimer);
            clearTimeout(doneTimer);
        };
    }, []);

    if (phase === 'done') return null;

    // Generate particles
    const particles = Array.from({ length: 20 }, (_, i) => ({
        delay: Math.random() * 3,
        size: 3 + Math.random() * 5,
        x: 5 + Math.random() * 90,
        duration: 3 + Math.random() * 4,
        color: i % 3 === 0
            ? 'rgba(5, 150, 105, 0.5)'
            : i % 3 === 1
                ? 'rgba(52, 211, 153, 0.4)'
                : 'rgba(16, 185, 129, 0.6)',
    }));

    const overlayStyle = {
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        overflow: 'hidden',
        opacity: phase === 'exiting' ? 0 : 1,
        visibility: phase === 'exiting' ? 'hidden' : 'visible',
        transition: 'opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1), visibility 0.7s ease',
        background: 'linear-gradient(135deg, #fafaf9 0%, #f1f5f9 50%, #e2e8f0 100%)',
    };

    const centerContainerStyle = {
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 320,
        height: 320,
    };

    // Pulsing glow behind moon
    const glowStyle = {
        position: 'absolute',
        width: '100%',
        height: '100%',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(5, 150, 105, 0.15) 0%, transparent 70%)',
        animation: 'glowPulse 2.5s ease-in-out infinite',
        transform: phase !== 'entering' ? 'scale(1)' : 'scale(0.5)',
        opacity: phase !== 'entering' ? 1 : 0,
        transition: 'all 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
    };

    // Moon icon
    const moonStyle = {
        fontSize: 140,
        color: fontsReady ? '#059669' : 'transparent',
        transition: 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        transform: phase !== 'entering' ? 'scale(1) rotate(0deg)' : 'scale(0.3) rotate(-40deg)',
        opacity: phase !== 'entering' ? 1 : 0,
        filter: phase === 'showing' ? 'drop-shadow(0 0 30px rgba(5, 150, 105, 0.4))' : 'none',
        fontVariationSettings: "'FILL' 1, 'wght' 200, 'GRAD' 0, 'opsz' 48",
        zIndex: 10,
        position: 'relative',
    };

    // Brand text
    const titleStyle = {
        fontSize: 38,
        fontWeight: 800,
        background: 'linear-gradient(135deg, #059669, #10b981, #34d399)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        letterSpacing: '-0.02em',
        marginTop: 28,
        opacity: phase === 'showing' ? 1 : 0,
        transform: phase === 'showing' ? 'translateY(0)' : 'translateY(15px)',
        transition: 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.3s',
    };

    const subtitleStyle = {
        fontSize: 16,
        fontWeight: 500,
        color: '#64748b',
        letterSpacing: '0.15em',
        textTransform: 'uppercase',
        marginTop: 8,
        opacity: phase === 'showing' ? 1 : 0,
        transform: phase === 'showing' ? 'translateY(0)' : 'translateY(10px)',
        transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.5s',
    };

    // Progress bar
    const progressTrackStyle = {
        width: 200,
        height: 3,
        borderRadius: 4,
        background: 'rgba(5, 150, 105, 0.1)',
        marginTop: 32,
        overflow: 'hidden',
        opacity: phase === 'showing' ? 1 : 0,
        transition: 'opacity 0.3s ease 0.6s',
    };

    const progressBarStyle = {
        height: '100%',
        borderRadius: 4,
        background: 'linear-gradient(90deg, #059669, #10b981, #34d399)',
        animation: 'progressFill 3.5s ease-out 0.5s forwards',
        width: 0,
    };

    return h('div', { ref: containerRef, style: overlayStyle, className: 'react-intro' },
        // Background radial gradients
        h('div', {
            style: {
                position: 'absolute', inset: 0,
                backgroundImage: `
                    radial-gradient(circle at 20% 30%, rgba(5, 150, 105, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(16, 185, 129, 0.06) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.04) 0%, transparent 70%)
                `,
                animation: 'bgPulse 4s ease-in-out infinite',
            }
        }),

        // Particles
        h('div', { style: { position: 'absolute', inset: 0, overflow: 'hidden' } },
            particles.map((p, i) => h(Particle, { key: i, ...p }))
        ),

        // Center container with orbiting dots and moon
        h('div', { style: centerContainerStyle },
            // Glow
            h('div', { style: glowStyle }),

            // Outer orbit ring (8 dots)
            h(OrbitRing, { count: 8, radius: 140, duration: 12, dotSize: 5 }),

            // Inner orbit ring (6 dots, reverse)
            h(OrbitRing, { count: 6, radius: 105, duration: 8, reverse: true, dotSize: 4 }),

            // Ripple rings
            h(RippleRing, { delay: 0, maxSize: 300 }),
            h(RippleRing, { delay: 1, maxSize: 300 }),
            h(RippleRing, { delay: 2, maxSize: 300 }),

            // Moon icon
            h('span', {
                className: 'material-symbols-outlined',
                style: moonStyle,
            }, 'dark_mode')
        ),

        // Brand text
        h('div', { style: { textAlign: 'center', position: 'relative', zIndex: 10 } },
            h('div', { style: titleStyle }, 'Al Huda'),
            h('div', { style: subtitleStyle }, 'Islamic Knowledge'),
        ),

        // Progress bar
        h('div', { style: progressTrackStyle },
            h('div', { style: progressBarStyle })
        )
    );
}

// ─────────────────────────────────────────────────────────
// Mount the React intro
// ─────────────────────────────────────────────────────────
function mountReactIntro() {
    const container = document.getElementById('reactIntroRoot');
    if (!container) return;

    const animationEnabled = localStorage.getItem('launchAnimation') !== 'false';
    if (!animationEnabled) {
        document.body.style.opacity = '1';
        document.body.classList.add('fonts-loaded');
        return;
    }

    const root = ReactDOM.createRoot(container);
    root.render(h(IntroAnimation, {
        onComplete: () => {
            // Reveal welcome screen elements with stagger
            const welcomeElements = document.querySelectorAll('#welcomeScreen > *');
            welcomeElements.forEach((el, index) => {
                el.classList.add('content-reveal', 'reveal-delay-' + Math.min(index + 1, 5));
            });
            // Clean up React mount after animation
            setTimeout(() => root.unmount(), 100);
        }
    }));
}

// Export
window.mountReactIntro = mountReactIntro;
