import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Label } from "../ui/label"

const signInSchema = z.object({
    email: z.email("Email is required"),
    password: z.string()
})

type SignInFormValues = z.infer<typeof signInSchema>

export function SignInForm({ className, ...props }: React.ComponentProps<"div">) {
    const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<SignInFormValues>({
        resolver: zodResolver(signInSchema)
    })


    const onSubmit = async (data: SignInFormValues) => {
        // calling api from backend to signin
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
                                <h1 className="text-2xl font-bold"> Welcome back </h1>
                                <p className="text-muted-foreground text-balance">
                                    Welcome! Please sign up to get started!
                                </p>
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

                            {/* Signin button */}
                            <Button type="submit" className="w-full" disabled={isSubmitting}>
                                Sign in
                            </Button>

                            <div className="text-center text-sm">
                                Don't have an account?{" "}
                                <a href="/signup" className="underline underline-offset-4">
                                    Sign up
                                </a>
                            </div>
                        </div>
                    </form>
                    <div className="bg-muted relative hidden md:block">
                        <img
                            src="/placeholder.png"
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