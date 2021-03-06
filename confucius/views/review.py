from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from confucius.models import Assignment, Conference, Review, Membership, Paper, PaperSelection
from confucius.forms import ReviewForm
from django.template import RequestContext
from django.contrib.auth.models import User



@login_required
def auto_assignment(request, pk_paper):
    paper = Paper.objects.get(pk=pk_paper)
    
    assignment = Assignment.objects.create(reviewer=User.objects.get(pk=2), paper=paper)
    assignment.save()
    
    return redirect('dashboard')
    
    
@login_required
def submit_review(request, pk_assignment):
    assignment = Assignment.objects.get(pk=pk_assignment)
    review = assignment.review
    form = ReviewForm(instance=review)

        
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)

        if form.is_valid():
            review = form.save()
            assignment.review = review
            
            if request.POST.__contains__('save_and_submit'):
                assignment.is_done = True
            
            assignment.save()
            return redirect('dashboard')

    return render_to_response('review/review_form.html', {'form':form, 'instance':review, 'assignment':assignment}, context_instance=RequestContext(request))
    
    
@login_required
def paper_selection_list(request):
    membership = Membership.objects.get(user=request.user, last_accessed=True)
    conference = membership.conference
        
    papers_not_assigned = Paper.objects.filter(conference=conference, assignments__isnull=True)
    assignments_without_reviews = Assignment.objects.filter(paper__conference=conference, is_done=False)
    papers_ready = Paper.objects.filter(conference=conference, assignments__is_done=True)
            
    return render_to_response('review/paper_selection_list.html', {'papers_not_assigned':papers_not_assigned, 'assignments_without_reviews':assignments_without_reviews, 'papers_ready':papers_ready, 'conference':conference}, context_instance=RequestContext(request))
    

@login_required
def read_reviews(request, pk_paper):
    paper = Paper.objects.get(pk=pk_paper)
    reviews = Review.objects.filter(assignment__paper=paper)
    
    if request.method == 'POST':
        if request.POST.__contains__('select_paper') or request.POST.__contains__('dont_select_paper') :
            selection, is_created = PaperSelection.objects.get_or_create(paper=paper, conference=paper.conference)
            if request.POST.__contains__('select_paper'):
                selection.is_selected = True
            elif request.POST.__contains__('dont_select_paper'):
                selection.is_selected = False
            
            selection.save()
            
            return redirect('paper_selection_list')

    return render_to_response('review/read_reviews.html', {'paper':paper, 'reviews':reviews}, context_instance=RequestContext(request))


@login_required
def finalize_selection(request):
    membership = Membership.objects.get(user=request.user, last_accessed=True)
    conference = membership.conference

    for paper_selection in conference.selections.all():
        paper_selection.is_submit = True
        paper_selection.save()

    conference.has_finalize_paper_selections = True
    conference.save()

    return redirect('dashboard')
