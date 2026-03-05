import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: ['log', 'error', 'warn'],
  });

  app.enableCors({ origin: '*' });

  const port = parseInt(process.env.PORT ?? '3000', 10);
  await app.listen(port);

  console.log('');
  console.log('  ☁  GCS Agent Console');
  console.log(`  → UI:    http://localhost:${port}`);
  console.log(`  → Agent: ${process.env.AGENT_API_URL ?? 'http://localhost:8080'}`);
  console.log('');
}

bootstrap();
