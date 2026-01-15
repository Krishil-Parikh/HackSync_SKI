import { useState, useCallback } from 'react';

/**
 * useChat - Custom hook for managing chat messages
 * 
 * Currently uses local state for frontend-only implementation.
 * Designed to be easily extended for backend integration.
 * 
 * TODO: Replace local state with API integration
 * TODO: Add WebSocket support for streaming responses
 * TODO: Add error handling and retry logic
 * TODO: Add message persistence (localStorage or backend)
 */

// Initial welcome message
const INITIAL_MESSAGES = [
    {
        id: 'welcome-1',
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant. I\'m here to help you with anything you need. Feel free to ask me questions, share ideas, or just have a conversation.',
        timestamp: new Date().toISOString(),
    },
];

// Mock AI responses for demo purposes
// TODO: Replace with actual API call
const MOCK_RESPONSES = [
    "That's a thoughtful question. Let me share my perspective on this...",
    "I appreciate you sharing that with me. Based on what you've said, I think...",
    "Interesting! Here's what I know about that topic...",
    "Great question! Let me break this down for you...",
    "I understand what you're looking for. Here's my take on it...",
];

/**
 * Generates a unique message ID
 * TODO: In production, this should come from the backend
 */
const generateId = () => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Simulates getting an AI response
 * TODO: Replace with actual API call to chat backend
 * 
 * @param {string} userMessage - The user's message
 * @returns {Promise<string>} - The AI's response
 */
const mockGetAIResponse = async (userMessage) => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 700));

    // Return a random mock response
    const randomIndex = Math.floor(Math.random() * MOCK_RESPONSES.length);
    return MOCK_RESPONSES[randomIndex];
};

/**
 * Custom hook for chat functionality
 * 
 * @returns {Object} Chat state and actions
 * @property {Array} messages - Array of message objects
 * @property {boolean} isLoading - Whether AI is generating a response
 * @property {Function} sendMessage - Function to send a new user message
 * @property {Function} clearMessages - Function to clear all messages
 */
export const useChat = () => {
    const [messages, setMessages] = useState(INITIAL_MESSAGES);
    const [isLoading, setIsLoading] = useState(false);

    /**
     * Sends a user message and gets AI response
     * 
     * @param {string} content - The message content
     * 
     * TODO: Integrate with chat API endpoint
     * TODO: Add support for streaming responses
     * TODO: Add error handling with user-friendly messages
     */
    const sendMessage = useCallback(async (content) => {
        if (!content.trim() || isLoading) return;

        // Create user message
        const userMessage = {
            id: generateId(),
            role: 'user',
            content: content.trim(),
            timestamp: new Date().toISOString(),
        };

        // Add user message to state
        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // TODO: Replace with actual API call
            // Example integration point:
            // const response = await fetch('/api/chat', {
            //   method: 'POST',
            //   headers: { 'Content-Type': 'application/json' },
            //   body: JSON.stringify({ message: content, conversationId }),
            // });
            // const data = await response.json();
            // const aiContent = data.message;

            const aiContent = await mockGetAIResponse(content);

            // Create AI message
            const aiMessage = {
                id: generateId(),
                role: 'assistant',
                content: aiContent,
                timestamp: new Date().toISOString(),
            };

            // Add AI message to state
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            // TODO: Add proper error handling
            console.error('Error getting AI response:', error);

            // Add error message
            const errorMessage = {
                id: generateId(),
                role: 'assistant',
                content: 'I apologize, but I encountered an error. Please try again.',
                timestamp: new Date().toISOString(),
                isError: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [isLoading]);

    /**
     * Clears all messages and resets to initial state
     */
    const clearMessages = useCallback(() => {
        setMessages(INITIAL_MESSAGES);
    }, []);

    return {
        messages,
        isLoading,
        sendMessage,
        clearMessages,
    };
};

export default useChat;
