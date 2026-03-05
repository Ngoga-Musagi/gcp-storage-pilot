import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  MessageBody,
  ConnectedSocket,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Logger } from '@nestjs/common';
import { Server, Socket } from 'socket.io';
import { ChatService } from './chat.service';

interface MessagePayload {
  message: string;
  sessionId: string;
}

@WebSocketGateway({
  cors: { origin: '*' },
  // No namespace — connects at /socket.io
})
export class ChatGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(ChatGateway.name);

  constructor(private readonly chatService: ChatService) {}

  handleConnection(client: Socket) {
    this.logger.log(`Connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Disconnected: ${client.id}`);
  }

  @SubscribeMessage('message')
  async handleMessage(
    @MessageBody() payload: MessagePayload,
    @ConnectedSocket() client: Socket,
  ): Promise<void> {
    const { message, sessionId } = payload;

    if (!message?.trim()) return;

    // Immediately acknowledge receipt
    client.emit('thinking', { type: 'thinking' });

    try {
      const response = await this.chatService.sendMessage(message, sessionId);
      client.emit('response', { type: 'response', message: response, sessionId });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.logger.error(`sendMessage failed: ${msg}`);
      client.emit('error_msg', { type: 'error', message: msg });
    }
  }

  @SubscribeMessage('health')
  async handleHealth(@ConnectedSocket() client: Socket): Promise<void> {
    try {
      const health = await this.chatService.getHealth();
      client.emit('health_response', health);
    } catch (err) {
      client.emit('health_response', {
        status: 'error',
        message: `Cannot reach backend: ${err.message}`,
      });
    }
  }

  @SubscribeMessage('new_session')
  async handleNewSession(@ConnectedSocket() client: Socket): Promise<void> {
    try {
      const sessionId = await this.chatService.newSession();
      client.emit('session_created', { sessionId });
    } catch (err) {
      // Fall back — let client generate its own UUID if backend unreachable
      client.emit('session_created', { sessionId: null, error: err.message });
    }
  }
}
