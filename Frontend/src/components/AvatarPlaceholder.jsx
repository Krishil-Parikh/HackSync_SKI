import { motion } from 'framer-motion';

/**
 * AvatarPlaceholder - Reserved space for future AI avatar
 * 
 * This component provides a styled container where an AI avatar
 * (video stream, canvas animation, or Lottie) can be integrated.
 * 
 * TODO: Replace with AI avatar video/canvas stream
 * TODO: Sync avatar animations with AI response timing
 * TODO: Add speaking/listening/thinking states
 */

const AvatarPlaceholder = () => {
    return (
        <div className="relative flex flex-col items-center justify-center h-full p-8">
            {/* Decorative background elements */}
            <div className="absolute inset-0 overflow-hidden">
                {/* Soft gradient orbs */}
                <motion.div
                    className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-accent-soft/40 blur-3xl"
                    animate={{
                        scale: [1, 1.1, 1],
                        opacity: [0.4, 0.6, 0.4],
                    }}
                    transition={{
                        duration: 8,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                />
                <motion.div
                    className="absolute bottom-1/4 right-1/4 w-48 h-48 rounded-full bg-sage-soft/50 blur-3xl"
                    animate={{
                        scale: [1, 1.15, 1],
                        opacity: [0.3, 0.5, 0.3],
                    }}
                    transition={{
                        duration: 10,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 1,
                    }}
                />
            </div>

            {/* Main avatar container */}
            <motion.div
                className="relative z-10"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
            >
                {/* Avatar frame with organic shape */}
                <motion.div
                    className="relative w-56 h-56 md:w-72 md:h-72 lg:w-80 lg:h-80"
                    animate={{
                        rotate: [0, 2, -2, 0],
                    }}
                    transition={{
                        duration: 12,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                >
                    {/* Outer glow ring */}
                    <div className="absolute inset-0 rounded-[40%_60%_55%_45%/50%_45%_55%_50%] bg-gradient-to-br from-accent/20 to-sage/20 blur-xl animate-breathe" />

                    {/* Main avatar area */}
                    <div className="absolute inset-4 rounded-[45%_55%_50%_50%/55%_50%_50%_45%] bg-gradient-to-br from-linen to-cream border border-stone/30 shadow-xl flex items-center justify-center overflow-hidden">
                        {/* 
              TODO: Replace this placeholder with actual avatar implementation
              Options:
              - Video element with avatar stream
              - Canvas for real-time avatar rendering
              - Lottie animation for pre-rendered avatar
              - Integration with avatar services (HeyGen, Synthesia, etc.)
            */}

                        {/* Placeholder content */}
                        <div className="text-center p-6">
                            {/* Artistic placeholder icon */}
                            <motion.div
                                className="w-20 h-20 md:w-24 md:h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-accent/30 to-sage/30 flex items-center justify-center"
                                animate={{
                                    scale: [1, 1.05, 1],
                                }}
                                transition={{
                                    duration: 4,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                }}
                            >
                                <svg
                                    className="w-10 h-10 md:w-12 md:h-12 text-charcoal/40"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={1.5}
                                        d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                                    />
                                </svg>
                            </motion.div>

                            <p className="text-sm text-slate font-light tracking-wide">
                                AI Avatar
                            </p>
                            <p className="text-xs text-mist mt-1">
                                Coming soon
                            </p>
                        </div>
                    </div>

                    {/* Subtle decorative dots */}
                    <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-accent/40" />
                    <div className="absolute -bottom-3 left-8 w-3 h-3 rounded-full bg-sage/50" />
                </motion.div>
            </motion.div>

            {/* Status indicator */}
            <motion.div
                className="mt-8 flex items-center gap-2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                <motion.div
                    className="w-2 h-2 rounded-full bg-sage"
                    animate={{
                        scale: [1, 1.3, 1],
                        opacity: [0.7, 1, 0.7],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                    }}
                />
                <span className="text-sm text-mist font-light tracking-wide">
                    Ready to assist
                </span>
            </motion.div>

            {/* Decorative text */}
            <motion.p
                className="absolute bottom-8 left-8 text-xs text-stone/60 font-light tracking-widest uppercase"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8, duration: 0.6 }}
            >
                Thoughtful AI
            </motion.p>
        </div>
    );
};

export default AvatarPlaceholder;
