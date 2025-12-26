import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "./ui/label"

export function SignupForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8">
            <div className="flex flex-col gap-6">

              {/* header - logo */}
              <div className="flex flex-col items-center text-center gap-2">
                <a href="/" className="mx-auto block w-fit text-center">
                  <img src="/logo.svg" alt="logo"/>
                </a>
                <h1 className="text-2xl font-bold"> Create new account </h1>
                <p className="text-muted-foreground text-balance">
                  Welcome! Please sign up to get started!
                </p>
              </div>

              {/* firstname and lastname */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="lastname" className="block-text-sm">
                    Lastname
                  </Label>
                  <Input type="text" id="lastname"/>
                  {/* todo: error message */}
                </div>
            
                <div className="space-y-2">
                  <Label htmlFor="firstname" className="block-text-sm">
                    Firstname
                  </Label>
                  <Input type="text" id="firstname"/>
                  {/* todo: error message */}
                </div>
              </div>
              
              {/* username */}
              <div className="flex flex-col gap-3">
                <div className="space-y-2">
                  <Label htmlFor="username" className="block-text-sm">
                    Username
                  </Label>
                  <Input type="text" id="username"/>
                  {/* todo: error message */}
                </div>
              </div>
              
              {/* email */}
              <div className="flex flex-col gap-3">
                <Label htmlFor="email" className="block-text-sm">
                  Email
                </Label>
                <Input type="text" id="email" placeholder="johndoe@example.com"/>
                {/* todo: error message */}
              </div>

              {/* password */}
              <div className="flex flex-col gap-3">
                <Label htmlFor="password" className="block-text-sm">
                  Password
                </Label>
                <Input type="text" id="password"/>
                {/* todo: error message */}
              </div>

              {/* Signin button */}
              <Button type="submit" className="w-full">
                Create new account?
              </Button>

              <div className="text-center text-sm">
                Do you have an account?
              </div>
            </div>
          </form>
          <div className="bg-muted relative hidden md:block">
            <img
              src="/placeholderSignUp.png"
              alt="Image"
              className="absolute top-1/2 -translate-y-1/2 object-cover"
            />
          </div>
        </CardContent>
      </Card>
      <div className="px-6 text-center">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  )
}
