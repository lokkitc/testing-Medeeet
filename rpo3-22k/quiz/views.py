from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Quiz, Question, QuizAttempt, Answer, Choice


def quiz_list(request):
    quizzes = Quiz.objects.filter(is_active=True)
    return render(request, 'quiz/quiz_list.html', {'quizzes': quizzes})


def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    user_attempts = QuizAttempt.objects.filter(quiz=quiz, user=request.user) if request.user.is_authenticated else []
    return render(request, 'quiz/quiz_detail.html', {
        'quiz': quiz,
        'user_attempts': user_attempts
    })


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    # Check if user has an incomplete attempt
    attempt = QuizAttempt.objects.filter(
        quiz=quiz, 
        user=request.user, 
        is_completed=False
    ).first()
    
    if not attempt:
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            total_points=sum(q.points for q in quiz.questions.all())
        )
    
    questions = quiz.questions.all()
    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions
    })


@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    attempt = get_object_or_404(QuizAttempt, quiz=quiz, user=request.user, is_completed=False)
    
    if request.method == 'POST':
        total_score = 0
        
        for question in quiz.questions.all():
            answer_text = request.POST.get(f'question_{question.id}')
            
            if question.question_type in ['single', 'multiple']:
                selected_choices = request.POST.getlist(f'question_{question.id}')
                if selected_choices:
                    choices = Choice.objects.filter(id__in=selected_choices)
                    correct_choices = set(choices.filter(is_correct=True))
                    selected_correct = set(choices.filter(is_correct=True))
                    
                    is_correct = correct_choices == selected_correct
                    points = question.points if is_correct else 0
                    
                    answer = Answer.objects.create(
                        attempt=attempt,
                        question=question,
                        is_correct=is_correct,
                        points_earned=points
                    )
                    answer.selected_choices.set(choices)
                    total_score += points
            else:
                # Text answer (simplified - in real implementation you'd need manual grading)
                answer = Answer.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=answer_text,
                    is_correct=True,  # Auto-mark as correct for demo
                    points_earned=question.points
                )
                total_score += question.points
        
        attempt.score = total_score
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        messages.success(request, f'Quiz submitted! Your score: {total_score}/{attempt.total_points}')
        return redirect('quiz:quiz_results', attempt_id=attempt.id)
    
    return redirect('quiz:take_quiz', quiz_id=quiz_id)


@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    answers = attempt.answers.all()
    return render(request, 'quiz/quiz_results.html', {
        'attempt': attempt,
        'answers': answers
    })
