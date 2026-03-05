import { Module } from '@nestjs/common';
import { ServeStaticModule } from '@nestjs/serve-static';
import { join } from 'path';
import { ChatModule } from './chat/chat.module';

@Module({
  imports: [
    // Serve public/index.html at GET /
    ServeStaticModule.forRoot({
      rootPath: join(__dirname, '..', 'public'),
      exclude: ['/api/(.*)', '/socket.io/(.*)'],
    }),
    ChatModule,
  ],
})
export class AppModule {}
