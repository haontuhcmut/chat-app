import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Label } from "../ui/label"

const signUpSchema = z.object({
  firstname: z.string().min(1, "What's your name?"),
  lastname: z.string().min(1, "What's your name?"),
  username: z.string().min(1, "Username is required"),
  email: z.email("Email is required"),
  password: z.string().min(8, "Password must be at least 8 characters")
    .regex(/[a-z]/, "Must contain a lowercase letter")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[0-9]/, "Must contain a number")
    .regex(/[^A-Za-z0-9]/, "Must contain a special character"),
  confirmPassword: z.string(),
}).refine(
  (data) => data.password === data.confirmPassword,
  {
    message: "Passwords do not match",
    path: ["confirmPassword"], // error shows here
  }
)

type SignUpFormValues = z.infer<typeof signUpSchema>

export function SignupForm({ className, ...props }: React.ComponentProps<"div">) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<SignUpFormValues>({
    resolver: zodResolver(signUpSchema)
  })


  const onSubmit = async (data: SignUpFormValues) => {
    // calling api from backend to signup
  }


  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0 border-border">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form className="p-6 md:p-8" onSubmit={handleSubmit(onSubmit)}>
            <div className="flex flex-col gap-6">

              {/* header - logo */}
              <div className="flex flex-col items-center text-center gap-2">
                <a href="/" className="mx-auto block w-fit text-center">
                  <img src="/logo.svg" alt="logo" />
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
                    Last name
                  </Label>
                  <Input type="text" id="lastname" placeholder="John" {...register("lastname")} />

                  {errors.lastname && (
                    <p className="text-destructive text-sm">
                      {errors.lastname.message}
                    </p>
                  )}

                </div>

                <div className="space-y-2">
                  <Label htmlFor="firstname" className="block-text-sm">
                    First name
                  </Label>
                  <Input type="text" id="firstname" placeholder="Doe" {...register("firstname")} />

                  {errors.firstname && (
                    <p className="text-destructive text-sm">
                      {errors.firstname.message}
                    </p>
                  )}

                </div>
              </div>

              {/* username */}
              <div className="flex flex-col gap-3">
                <div className="space-y-2">
                  <Label htmlFor="username" className="block-text-sm">
                    Username
                  </Label>
                  <Input type="text" id="username" placeholder="johndoe" {...register("username")} />

                  {errors.username && (
                    <p className="text-destructive text-sm">
                      {errors.username.message}
                    </p>
                  )}

                </div>
              </div>

              {/* email */}
              <div className="flex flex-col gap-3">
                <Label htmlFor="email" className="block-text-sm">
                  Email
                </Label>
                <Input type="text" id="email" placeholder="johndoe@example.com" {...register("email")} />

                {errors.email && (
                  <p className="text-destructive text-sm">
                    {errors.email.message}
                  </p>
                )}

              </div>

              {/* password */}
              <div className="flex flex-col gap-3">
                <Label htmlFor="password" className="block-text-sm">
                  Password
                </Label>
                <Input type="text" id="password"  {...register("password")} />

                {errors.password && (
                  <p className="text-destructive text-sm">
                    {errors.password.message}
                  </p>
                )}
              </div>

              {/* confirm password */}
              <div className="flex flex-col gap-3">
                <Label htmlFor="confirm-password" className="block-text-sm">
                  Confirm password
                </Label>
                <Input type="text" id="confirm-password" {...register("confirmPassword")} />

                {errors.confirmPassword && (
                  <p className="text-destructive text-sm">
                    {errors.confirmPassword.message}
                  </p>
                )}
              </div>

              {/* Signup button */}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                Create new account?
              </Button>

              <div className="text-center text-sm">
                Do you have an account?{" "}
                <a href="/signin" className="underline underline-offset-4">
                  Sign in
                </a>
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
      <div className="text-xs text-balance px-6 text-center *:[a]:hover:text-primary text-muted-foreground *:[a]:underline *:[a]:underline-offeset-4">
        By clicking continue, you agree to our <a href="#">Terms of Service</a>{" "}
        and <a href="#">Privacy Policy</a>.
      </div>
    </div>
  )
}
