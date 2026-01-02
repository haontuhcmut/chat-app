import {create} from 'zustand'
import {toast} from 'sonner'
import { authService } from '@/services/authService'

export const useAuthStore = create((set, get) => ({
    accessToken: null,
    user: null,
    loading: false

    signUp: async (username, password, confirm_password, email, firstName, lastName) => {
        try {
            set({loading: true})
            //api call
            await authService.signUp(username, password, confirm_password, email, firstName, lastName)
            toast.success("Registration successful. Redirecting to login page.")
        } catch (error) {
            console.error(error);
            toast.error('Registration failed')
        }
    }
}))