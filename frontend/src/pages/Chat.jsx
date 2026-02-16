import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '../services/chatService';
import MessageList from '../components/Chat/MessageList';
import MessageInput from '../components/Chat/MessageInput';
import SourcesDisplay from '../components/Chat/SourcesDisplay';
import ChatHistorySidebar from '../components/Chat/ChatHistorySidebar';
import Loader from '../components/Common/Loader';

const Chat = () => {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const queryClient = useQueryClient();

  // Fetch chat sessions
  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: chatService.getSessions
  });

  // Ask question mutation
  const askMutation = useMutation({
    mutationFn: ({ question, mode }) => 
      chatService.askQuestion(question, currentSession?.id, mode),
    onSuccess: (data) => {
      // Add to messages
      setMessages(prev => [
        ...prev,
        { role: 'user', content: data.question },
        { role: 'assistant', content: data.answer }
      ]);
      
      setSources({
        documents: data.document_results,
        web: data.web_results,
        sources_used: data.sources_used
      });
      
      setIsLoading(false);
      
      // Invalidate sessions to refresh history
      queryClient.invalidateQueries(['chatSessions']);
    }
  });

  // Create new session
  const createSessionMutation = useMutation({
    mutationFn: (name) => chatService.createSession(name),
    onSuccess: (data) => {
      setCurrentSession(data);
      setMessages([]);
      setSources(null);
      queryClient.invalidateQueries(['chatSessions']);
    }
  });

  const handleSendMessage = async (question, mode = 'auto') => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    askMutation.mutate({ question, mode });
  };

  const handleNewChat = () => {
    createSessionMutation.mutate('New Chat');
  };

  const handleSelectSession = (session) => {
    setCurrentSession(session);
    // Load session history
    if (session.history) {
      const formattedMessages = session.history.flatMap(msg => [
        { role: 'user', content: msg.question },
        { role: 'assistant', content: msg.answer }
      ]);
      setMessages(formattedMessages);
    } else {
      setMessages([]);
    }
    setSources(null);
  };

  return (
    <div className="flex h-[calc(100vh-120px)]">
      {/* Chat History Sidebar */}
      <ChatHistorySidebar
        sessions={sessions || []}
        currentSession={currentSession}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        isLoading={sessionsLoading}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-lg ml-4 p-4">
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center py-20">
              <h3 className="text-2xl font-cinzel text-gray-700 mb-4">
                Welcome to 1421 AI Research
              </h3>
              <p className="text-gray-500">
                Ask any question about Chinese exploration, Zheng He's voyages, or the 1421 theory.
              </p>
            </div>
          ) : (
            <MessageList messages={messages} />
          )}
          
          {isLoading && (
            <div className="flex justify-center py-4">
              <Loader />
            </div>
          )}
        </div>

        {/* Sources Display */}
        {sources && <SourcesDisplay sources={sources} />}

        {/* Input Area */}
        <div className="mt-4 border-t pt-4">
          <MessageInput 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default Chat;