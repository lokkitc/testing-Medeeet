from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Assignment, Submission, Comment


def assignment_list(request):
    assignments = Assignment.objects.filter(is_published=True).order_by('due_date')
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})


def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    user_submission = None
    if request.user.is_authenticated:
        user_submission = Submission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
    
    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'user_submission': user_submission
    })


@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    # Check if already submitted
    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()
    
    if existing_submission:
        messages.error(request, 'You have already submitted this assignment!')
        return redirect('assignments:assignment_detail', assignment_id=assignment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        file_attachment = request.FILES.get('file_attachment')
        
        is_late = timezone.now() > assignment.due_date
        
        submission = Submission.objects.create(
            assignment=assignment,
            student=request.user,
            content=content,
            file_attachment=file_attachment,
            is_late=is_late
        )
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('assignments:submission_detail', submission_id=submission.id)
    
    return render(request, 'assignments/submit_assignment.html', {'assignment': assignment})


@login_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, student=request.user)
    comments = submission.comments.all().order_by('created_at')
    return render(request, 'assignments/submission_detail.html', {
        'submission': submission,
        'comments': comments
    })


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    
    # In a real app, you'd check if user is instructor/staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to grade submissions!')
        return redirect('assignments:submission_detail', submission_id=submission_id)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback')
        
        submission.score = score
        submission.feedback = feedback
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, 'Submission graded successfully!')
        return redirect('assignments:submission_detail', submission_id=submission_id)
    
    return render(request, 'assignments/grade_submission.html', {'submission': submission})
