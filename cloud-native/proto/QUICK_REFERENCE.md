# Protocol Buffers Quick Reference

## 🚀 Quick Commands

```bash
# Install tools (first time only)
make proto-install

# Generate code from proto files
make proto-gen

# View all available commands
make help
```

## 📁 File Locations

| Item | Location |
|------|----------|
| Proto definitions | `proto/*/*.proto` |
| Generated Go code | `shared/proto-gen/go/` |
| Generated TypeScript | `frontend/src/proto-gen/` |
| Generation scripts | `scripts/generate-proto.*` |

## 🔧 Services

| Service | Proto File | Purpose |
|---------|-----------|---------|
| Auth | `proto/auth/auth.proto` | Authentication & authorization |
| Video | `proto/video/video.proto` | Video upload & streaming |
| Homework | `proto/homework/homework.proto` | Assignments & grading |
| Analytics | `proto/analytics/analytics.proto` | User activity tracking |
| Collaboration | `proto/collaboration/collaboration.proto` | Study groups & chat |
| PDF | `proto/pdf/pdf.proto` | PDF document management |

## 💻 Code Examples

### Go Server
```go
import pb "metlab/proto/auth"

type server struct {
    pb.UnimplementedAuthServiceServer
}

func (s *server) TeacherLogin(ctx context.Context, req *pb.LoginRequest) (*pb.AuthResponse, error) {
    return &pb.AuthResponse{Token: "..."}, nil
}
```

### Go Client
```go
import pb "metlab/proto/auth"

conn, _ := grpc.Dial("localhost:50051", grpc.WithInsecure())
client := pb.NewAuthServiceClient(conn)
resp, _ := client.TeacherLogin(ctx, &pb.LoginRequest{...})
```

### TypeScript
```typescript
import { AuthServiceClient } from './proto-gen/auth/auth';

const client = new AuthServiceClient('http://localhost:8080');
const response = await client.TeacherLogin({...});
```

## 🔄 Workflow

1. **Modify** proto file in `proto/*/`
2. **Generate** code: `make proto-gen`
3. **Update** service implementations
4. **Test** changes
5. **Commit** proto files (not generated code)

## ⚠️ Important Rules

- ❌ Never edit generated code
- ❌ Never reuse field numbers
- ✅ Add new fields, don't modify existing
- ✅ Use comments to document changes
- ✅ Regenerate after every proto change

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `protoc not found` | Run `make proto-install` |
| `plugin not found` | Install Go/TS plugins (see PROTO_SETUP.md) |
| Generation fails | Check proto syntax, ensure tools installed |
| Import errors | Regenerate all: `make proto-gen` |

## 📚 Documentation

- Full setup guide: `PROTO_SETUP.md`
- Proto documentation: `proto/README.md`
- Implementation summary: `PROTO_IMPLEMENTATION_SUMMARY.md`

## 🆘 Need Help?

1. Check `PROTO_SETUP.md` for detailed instructions
2. Review `proto/README.md` for examples
3. Run `make help` for available commands
