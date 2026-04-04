content = open('backend/quiz/quiz_generator.py').read()
content = content.replace('}, timeout=90)', '}, timeout=120)')
content = content.replace("if quiz_data and 'questions' in quiz_data:", "if quiz_data:"
                    if 'questions' not in quiz_data:"
                        for key in quiz_data:"
                            if isinstance(quiz_data[key], list):"
                                quiz_data['questions'] = quiz_data[key]"
                                break"
                    if 'questions' in quiz_data:")
open('backend/quiz/quiz_generator.py', 'w').write(content)
print('Done!')
