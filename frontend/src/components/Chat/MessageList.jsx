import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const MessageList = ({ messages }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="space-y-4">
      {messages.map((msg, index) => (
        <div
          key={index}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] rounded-lg p-4 ${
              msg.role === 'user'
                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                : 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-200'
            }`}
          >
            {msg.role === 'assistant' ? (
              <ReactMarkdown className="prose prose-sm max-w-none">
                {msg.content}
              </ReactMarkdown>
            ) : (
              <p className="text-sm">{msg.content}</p>
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;